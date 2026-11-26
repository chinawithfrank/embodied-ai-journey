// Audio bench test for the original ESP32-S3 development-board wiring.
#include <math.h>
#include <stdint.h>
#include "sdkconfig.h"
#include "driver/gpio.h"
#include "driver/i2s_std.h"
#include "esp_check.h"
#include "esp_log.h"

enum { RATE = 16000, BLOCK = 160, TONE = 1920, PERIOD = 5 * RATE };
static int32_t stereo[BLOCK * 2];

void app_main(void)
{
    const int inactive[] = {1, 2, 38, 39, 40};
    gpio_config_t off = {
        .mode = GPIO_MODE_INPUT_OUTPUT, // Enable pad readback for bench diagnostics.
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
    };
    for (size_t i = 0; i < sizeof(inactive) / sizeof(inactive[0]); ++i) {
        ESP_ERROR_CHECK(gpio_set_level(inactive[i], 0));
        off.pin_bit_mask |= 1ULL << inactive[i];
    }

    // gpio_config also selects the GPIO function on multiplexed JTAG pads.
    ESP_ERROR_CHECK(gpio_config(&off));

#if CONFIG_FAN_TEST_MICROPHONE
    ESP_ERROR_CHECK(gpio_set_level(GPIO_NUM_15, 0));
    gpio_config_t mute = {.pin_bit_mask = 1ULL << GPIO_NUM_15, .mode = GPIO_MODE_OUTPUT};
    ESP_ERROR_CHECK(gpio_config(&mute));
    i2s_chan_handle_t rx;
    i2s_chan_config_t channel = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_AUTO, I2S_ROLE_MASTER);
    ESP_ERROR_CHECK(i2s_new_channel(&channel, NULL, &rx));
    i2s_std_config_t config = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {.mclk = I2S_GPIO_UNUSED, .bclk = GPIO_NUM_41, .ws = GPIO_NUM_42,
                     .dout = I2S_GPIO_UNUSED, .din = GPIO_NUM_47},
    };
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(rx, &config));
    // INMP441 releases the data line in the unused channel.
    ESP_ERROR_CHECK(gpio_set_pull_mode(GPIO_NUM_47, GPIO_PULLDOWN_ONLY));
    ESP_ERROR_CHECK(i2s_channel_enable(rx));
    for (;;) {
        double sum = 0, squares = 0;
        int32_t minimum = INT32_MAX, maximum = INT32_MIN;
        for (int frames = 0; frames < RATE; frames += BLOCK) {
            size_t bytes;
            ESP_ERROR_CHECK(i2s_channel_read(rx, stereo, sizeof(stereo), &bytes, 1000));
            ESP_ERROR_CHECK(bytes == sizeof(stereo) ? ESP_OK : ESP_ERR_INVALID_SIZE);
            for (int i = 0; i < BLOCK; ++i) {
                int32_t sample = stereo[2 * i] >> 8;
                if (sample < minimum) minimum = sample;
                if (sample > maximum) maximum = sample;
                sum += sample;
                squares += (double)sample * sample;
            }
        }
        double mean = sum / RATE;
        double rms = sqrt(fmax(0, squares / RATE - mean * mean));
        ESP_LOGI("mic", "left ac_rms=%.0f peak_to_peak=%ld GPIO38=%d GPIO39=%d",
                 rms, (long)(maximum - minimum), gpio_get_level(GPIO_NUM_38), gpio_get_level(GPIO_NUM_39));
    }
#else
    i2s_chan_handle_t tx;
    i2s_chan_config_t channel = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_AUTO, I2S_ROLE_MASTER);
    channel.auto_clear = true;
    ESP_ERROR_CHECK(i2s_new_channel(&channel, &tx, NULL));
    i2s_std_config_t config = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {.mclk = I2S_GPIO_UNUSED, .bclk = GPIO_NUM_41, .ws = GPIO_NUM_42,
                     .dout = GPIO_NUM_15, .din = I2S_GPIO_UNUSED},
    };
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(tx, &config));
    ESP_ERROR_CHECK(i2s_channel_enable(tx));
    unsigned count = 0;
    for (;;) {
        for (int start = 0; start < PERIOD; start += BLOCK) {
            for (int i = 0; i < BLOCK; ++i) {
                int frame = start + i;
                int32_t sample = 0;
                if (frame < TONE) {
                    float envelope = fminf(1.f, fminf(frame, TONE - 1 - frame) / 160.f);
                    sample = (int32_t)(INT32_MAX * 0.02f * envelope *
                                      sinf(6.2831853f * 800.f * frame / RATE));
                }
                stereo[2*i] = stereo[2*i + 1] = sample;
            }
            size_t bytes;
            ESP_ERROR_CHECK(i2s_channel_write(tx, stereo, sizeof(stereo), &bytes, 1000));
            ESP_ERROR_CHECK(bytes == sizeof(stereo) ? ESP_OK : ESP_ERR_INVALID_SIZE);
            if (start + BLOCK == TONE) {
                ESP_LOGI("speaker", "Tone %u queued; right pad levels GPIO38=%d GPIO39=%d",
                         ++count, gpio_get_level(GPIO_NUM_38), gpio_get_level(GPIO_NUM_39));
            }
        }
    }
#endif
}
