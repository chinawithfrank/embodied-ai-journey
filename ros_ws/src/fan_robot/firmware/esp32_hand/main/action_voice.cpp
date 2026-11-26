#include "action_voice.hpp"
#include <algorithm>
#include <cstdint>
#include "driver/i2s_std.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

namespace action_voice {
enum class Cue { none, target, left, right, forward, backward };
#define PCM(name) extern const int16_t name[] asm("_binary_" #name "_pcm_start"); \
                  extern const int16_t name##_end[] asm("_binary_" #name "_pcm_end")
PCM(target); PCM(left); PCM(right); PCM(forward); PCM(backward);
struct Clip { const int16_t *begin, *end; const char *text; };
static const Clip clips[] = {{nullptr,nullptr,""}, {target,target_end,"发现目标"},
    {left,left_end,"左转"}, {right,right_end,"右转"}, {forward,forward_end,"前进"},
    {backward,backward_end,"后退"}};
static portMUX_TYPE lock = portMUX_INITIALIZER_UNLOCKED;
static bool target_pending;
static Cue pending, last_motion;
static int64_t last_seen = -1000000, last_moving = -1000000;
static constexpr int64_t release_us = 800000;

void observe(bool found) {
    const auto now = esp_timer_get_time();
    portENTER_CRITICAL(&lock);
    if (found) {
        if (now - last_seen >= release_us) target_pending = true;
        last_seen = now;
    } else {
        if (now - last_seen >= release_us) target_pending = false;
    }
    portEXIT_CRITICAL(&lock);
}

void motion(int l, int r) {
    const auto now = esp_timer_get_time();
    Cue cue = Cue::none;
    if (l > 0 && r > 0) cue = Cue::forward;
    else if (l < 0 && r < 0) cue = Cue::backward;
    else if (l < 0 && r > 0) cue = Cue::left;
    else if (l > 0 && r < 0) cue = Cue::right;
    portENTER_CRITICAL(&lock);
    if (cue != Cue::none) {
        if (cue != last_motion) pending = cue;
        last_motion = cue;
        last_moving = now;
    } else if (now-last_moving >= release_us) {
        last_motion = Cue::none;
    }
    portEXIT_CRITICAL(&lock);
}

static void playback(void *arg) {
    auto tx = static_cast<i2s_chan_handle_t>(arg);
    int32_t stereo[320];
    for (;;) {
        Cue cue;
        portENTER_CRITICAL(&lock);
        if (target_pending) { cue = Cue::target; target_pending = false; }
        else { cue = pending; pending = Cue::none; }
        portEXIT_CRITICAL(&lock);
        if (cue == Cue::none) { vTaskDelay(pdMS_TO_TICKS(20)); continue; }
        const auto &clip = clips[static_cast<unsigned>(cue)];
        for (auto p = clip.begin; p < clip.end;) {
            const auto n = std::min<ptrdiff_t>(160, clip.end-p);
            for (int i=0; i<n; ++i) stereo[2*i] = stereo[2*i+1] = int32_t(p[i])*8192;
            size_t bytes = 0;
            if (i2s_channel_write(tx, stereo, n*8, &bytes, 500) != ESP_OK || bytes != size_t(n)*8) {
                ESP_LOGE("action_voice", "Playback interrupted");
                break;
            }
            p += n;
            if (p == clip.end) ESP_LOGI("action_voice", "%s", clip.text);
        }
    }
}

void start() {
    i2s_chan_handle_t tx = nullptr;
    i2s_chan_config_t chan = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_AUTO, I2S_ROLE_MASTER);
    chan.auto_clear = true;
    i2s_std_config_t cfg = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(16000),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT,I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {.mclk=I2S_GPIO_UNUSED,.bclk=GPIO_NUM_41,.ws=GPIO_NUM_42,
                     .dout=GPIO_NUM_15,.din=I2S_GPIO_UNUSED,.invert_flags={}},
    };
    if (i2s_new_channel(&chan,&tx,nullptr) == ESP_OK &&
        i2s_channel_init_std_mode(tx,&cfg) == ESP_OK && i2s_channel_enable(tx) == ESP_OK) {
        if (xTaskCreate(playback,"action_voice",4096,tx,2,nullptr) == pdPASS) {
            ESP_LOGI("action_voice","Mandarin prompts ready");
            return;
        }
        i2s_channel_disable(tx);
    }
    if (tx) i2s_del_channel(tx);
    ESP_LOGE("action_voice","Audio unavailable; robot control continues");
}
}
