#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/stdio.h"
#include "hardware/spi.h"
#include "hardware/uart.h"
#include "bsp/board_api.h"

#include "st7789.h"

#include "tusb.h"
#include "device/usbd.h"
#include "tusb_config.h"

#define BUTTON1_PIN 13
#define BUTTON2_PIN 14

#define UART_ID     uart0
#define BAUD_RATE   9600
#define UART_TX_PIN 0
#define UART_RX_PIN 1
#define DATA_BITS   8 // 8N1
#define PARITY      UART_PARITY_NONE
#define STOP_BITS   1

typedef enum _transceiver_mode_t {
    RECEIVER,
    TRANSMITTER,
} transceiver_mode_t;

const struct st7789_config lcd_config = {
    .spi = spi1,
    .gpio_din = 11,
    .gpio_clk = 10,
    .gpio_cs = 9,
    .gpio_dc = 8,
    .gpio_rst = 12,
    .gpio_bl = 13,
};

// LCD rotation {0x60, 240, 135, 40, 53},
const uint16_t lcd_width = 240;
const uint16_t lcd_height = 135;

uint8_t buffer[128];
transceiver_mode_t mode = RECEIVER;

int main()
{
    // ---------------------- USB -------------------------
    // Initialize TinyUSB stack
    board_init();
    tusb_init();

    // TinyUSB board init callback after init
    if (board_init_after_tusb)
    {
        board_init_after_tusb();
    }

    // let pico sdk use the first cdc interface for std io
    stdio_init_all();

    // ---------------------- UART -------------------------
    uart_init(UART_ID, BAUD_RATE);
    uart_set_hw_flow(UART_ID, false, false);
    uart_set_format(UART_ID, DATA_BITS, STOP_BITS, PARITY);
    uart_set_fifo_enabled(UART_ID, false);

    gpio_set_function(UART_TX_PIN, UART_FUNCSEL_NUM(UART_ID, UART_TX_PIN));
    gpio_set_function(UART_RX_PIN, UART_FUNCSEL_NUM(UART_ID, UART_RX_PIN));

    // ---------------------- Buttons -------------------------
    gpio_init(BUTTON1_PIN);
    gpio_set_dir(BUTTON1_PIN, GPIO_IN);
    gpio_set_pulls(BUTTON1_PIN, true, false);

    gpio_init(BUTTON2_PIN);
    gpio_set_dir(BUTTON2_PIN, GPIO_IN);
    gpio_set_pulls(BUTTON2_PIN, true, false);

    // ---------------------- Screen -------------------------
    st7789_init(&lcd_config, lcd_width, lcd_height);
    st7789_fill(0xffff); // make screen white

    uint64_t delay = 0;
    while (1)
    {
        // tinyusb device task
        tud_task();

        if (gpio_get(BUTTON1_PIN) == false)
        {
            delay = 0;
            mode = RECEIVER;
            st7789_fill(0xffff);
            printf("New mode: receiver \n");
        }

        if (gpio_get(BUTTON2_PIN) == false)
        {
            delay = 0;
            mode = TRANSMITTER;
            st7789_fill(0x0000);
            printf("New mode: transmitter \n");
        }

        delay++;

        if (mode == RECEIVER)
        {
            while (uart_is_readable(UART_ID))
            {
                char received_char = uart_getc(UART_ID);
                tud_cdc_n_write_char(1, received_char);
                printf("Data received");
            }

            if (delay > 1000000)
            {
                delay = 0;
                printf("Periodic echo - reception \n");
            }
        }

        if (mode == TRANSMITTER)
        {
            if (delay > 1000000)
            {
                delay = 0;

                sprintf((char *)buffer, "dupa \n\r");
                for (int i = 0; i < strlen((const char *)buffer); i++)
                {
                    uart_putc(UART_ID, buffer[i]);
                    tud_cdc_n_write_char(1, buffer[i]); //
                    tud_cdc_write_flush();
                }

                // for (int i = 0; i < 128; i++)
                // {
                //     uart_putc(UART_ID, buffer[i]);
                // }

                printf("Periodic echo - transmission \n");
            }
        }
    }
}
