idf_component_register(SRCS "app_main.cpp"
    INCLUDE_DIRS "." "../../esp32_camera"
    REQUIRES esp32-camera hand_detect esp_wifi esp_event esp_netif
             nvs_flash esp_http_server esp_timer json esp_psram)
target_compile_features(${COMPONENT_LIB} PRIVATE cxx_std_17)
