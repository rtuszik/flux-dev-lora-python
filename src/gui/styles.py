from nicegui import ui, ElementFilter
from loguru import logger


class Styles:
    def setup_custom_styles():
        logger.debug("Setting up custom styles")
        ui.add_head_html("""
            <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:ital,wght@0,100..700;1,100..700&display=swap" rel="stylesheet">
            <style>
                body, .q-field__native, .q-btn__content, .q-item__label {
                    font-family: 'Roboto Mono', sans-serif !important;
                } 
                .modern-card {
                    border-radius: 15px;
                    box-shadow: 10px 10px 5px rgba(0, 0, 0, 0.1);
                    transition: all 0.3s ease;
                }
                .modern-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 10px 10px 5px rgba(0, 0, 0, 0.15);
                }
                .modern-button {
                    border-radius: 8px;
                    text-transform: uppercase;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                }
                @keyframes pulse {
                    0%, 100% {
                        opacity: 1;
                    }
                    50% {
                        opacity: .5;
                    }
                }
                }
            </style>
        """)

        # ui.add_css("""
        #         .bg {
        #             color: red;
        #         }
        #     """)
        ui.colors(
            dark="#303446",  # Crust (Closest: Grey-9)
            primary="#8aadf4",  # Blue (Closest: Blue-4)
            positive="#a6d189",  # Green (Closest: Green-4)
            negative="#e78284",  # Maroon (Closest: Red-3)
            secondary="#f38ba8",  # Red (Closest: Red-4)
            accent="#f5bde6",  # Pink (Closest: Pink-3)
            info="#89dceb",  # Sky (Closest: Cyan-4)
            warning="#f0a988",  # Peach (Closest: Orange-4)
        )

    def stylefilter(self):
        ElementFilter(kind=ui.label).classes("mt-0")

        ElementFilter(kind=ui.card).classes("dark:bg-[#181825] bg-[#ccd0da]")
