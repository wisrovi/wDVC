"""Gradio web interface for DVC queue management.

This module provides a user-friendly web interface for submitting files to
the DVC processing queue and monitoring their status.
"""

from datetime import datetime

import gradio as gr

from src.scripts.api.app.worker_queue import (
    get_complete_queue,
    get_Status_item,
    put_in_queue,
    get_complete_set,
)


def get_register_set() -> str:
    """
    Prints the status of each item in the complete set in a human-readable form.

    Maps numeric scores to statuses ("Pending", "Processing", "Completed", "Failed")
    and fetches additional information for each item using helper functions.

    Helper functions:
        - get_complete_set(): returns a list of (item, score) tuples
        - get_Status_item(item): returns additional status info for the item

    Returns:
        str: always returns an empty string
    """
    # the mapper is used to convert the score to a human readable string
    mapper = {
        0: "Pendiente",
        1: "Procesando",
        2: "Completado",
        3: "Fallido",
    }

    items = get_complete_set()
    for item, score in items:
        status_data = get_Status_item(item)
        print(f"Item: {item}, Status: {mapper[int(score)]}, Status: {status_data}")
    return ""


def add_to_queue(path: str) -> str:
    """Adds a new element to the processing queue.

    Args:
        path: File system path of the file or directory to process.

    Returns:
        HTML output with visual message and structured data.
    """
    try:
        new_item = put_in_queue(path)
        time_start = new_item.get("metadata", {}).get("time_start", "N/A")
        id_value = new_item.get("id", "N/A")
        queue_size = new_item.get("queue_size", "N/A")

        print(f"New item ({path}) added in position: {queue_size}")

        html_output = f"""
        <div style="background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%); 
                    border-left: 5px solid #10b981; 
                    padding: 20px; 
                    border-radius: 12px; 
                    color: #f1f5f9; 
                    font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    box-shadow: 0 4px 20px rgba(30, 64, 175, 0.2);
                    margin: 10px 0;">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <span style="font-size: 2em; margin-right: 15px; filter: brightness(1.2);">🎉</span>
                <strong style="font-size: 1.4em; color: #f0f9ff;">Successfully Added to Queue!</strong>
            </div>
            <div style="background: rgba(15, 23, 42, 0.4); padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid rgba(148, 163, 184, 0.1);">
                <p style="margin: 8px 0; color: #e2e8f0;"><strong style="color: #94a3b8;">📁 Path:</strong> <span style="color: #f1f5f9; font-family: monospace;">{path}</span></p>
                <p style="margin: 8px 0; color: #e2e8f0;"><strong style="color: #94a3b8;">🆔 ID:</strong> <span style="color: #f1f5f9; font-family: monospace;">{id_value}</span></p>
                <p style="margin: 8px 0; color: #e2e8f0;"><strong style="color: #94a3b8;">🆔 Queue position:</strong> <span style="color: #f1f5f9; font-family: monospace;">{queue_size}</span></p>
                <p style="margin: 8px 0; color: #e2e8f0;"><strong style="color: #94a3b8;">⏰ Started:</strong> <span style="color: #f1f5f9;">{time_start}</span></p>
            </div>
        </div>
        """
        return html_output

    except FileNotFoundError as e:
        error_html = f"""
        <div style="background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%); 
                    color: #fef2f2; 
                    padding: 20px; 
                    border-radius: 12px; 
                    font-family: 'Inter', 'Segoe UI', sans-serif;
                    box-shadow: 0 4px 20px rgba(127, 29, 29, 0.2);
                    border: 1px solid rgba(254, 242, 242, 0.1);">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 2em; margin-right: 15px; filter: brightness(1.2);">❌</span>
                <div>
                    <strong style="font-size: 1.3em; color: #fecaca;">File Not Found</strong>
                    <p style="margin: 8px 0; color: #fca5a5; opacity: 0.9;">{str(e)}</p>
                </div>
            </div>
        </div>
        """
        return error_html

    except Exception as e:
        error_html = f"""
        <div style="background: linear-gradient(135deg, #78350f 0%, #92400e 100%); 
                    color: #fef3c7; 
                    padding: 20px; 
                    border-radius: 12px; 
                    font-family: 'Inter', 'Segoe UI', sans-serif;
                    box-shadow: 0 4px 20px rgba(120, 53, 15, 0.2);
                    border: 1px solid rgba(254, 243, 199, 0.1);">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 2em; margin-right: 15px; filter: brightness(1.2);">⚠️</span>
                <div>
                    <strong style="font-size: 1.3em; color: #fde68a;">Unexpected Error</strong>
                    <p style="margin: 8px 0; color: #fcd34d; opacity: 0.9;">{str(e)}</p>
                </div>
            </div>
        </div>
        """
        return error_html


def get_status(item_id: str) -> str:
    """Retrieves the status of an element in the queue by its ID.

    Args:
        item_id: ID of the element to query.

    Returns:
        HTML output with visualization and status data.
    """
    try:
        if not item_id.strip():
            error_html = """
            <div style="background: linear-gradient(135deg, #78350f 0%, #92400e 100%); 
                        color: #fef3c7; 
                        padding: 20px; 
                        border-radius: 12px; 
                        font-family: 'Inter', 'Segoe UI', sans-serif;
                        box-shadow: 0 4px 20px rgba(120, 53, 15, 0.2);
                        border: 1px solid rgba(254, 243, 199, 0.1);">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 2em; margin-right: 15px; filter: brightness(1.2);">⚠️</span>
                    <div>
                        <strong style="font-size: 1.3em; color: #fde68a;">ID Required</strong>
                        <p style="margin: 8px 0; color: #fcd34d; opacity: 0.9;">Please enter an item ID to check status</p>
                    </div>
                </div>
            </div>
            """
            return error_html

        status_data = get_Status_item(item_id.strip())

        if not status_data:
            error_html = f"""
            <div style="background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%); 
                        color: #fef2f2; 
                        padding: 20px; 
                        border-radius: 12px; 
                        font-family: 'Inter', 'Segoe UI', sans-serif;
                        box-shadow: 0 4px 20px rgba(127, 29, 29, 0.2);
                        border: 1px solid rgba(254, 242, 242, 0.1);">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 2em; margin-right: 15px; filter: brightness(1.2);">🔍</span>
                    <div>
                        <strong style="font-size: 1.3em; color: #fecaca;">Item Not Found</strong>
                        <p style="margin: 8px 0; color: #fca5a5; opacity: 0.9;">No item found with ID: {item_id}</p>
                    </div>
                </div>
            </div>
            """
            return error_html

        # Determine base color according to status
        status_colors = {
            "completed": "linear-gradient(135deg, #14532d 0%, #166534 100%)",
            "processing": "linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%)",
            "pending": "linear-gradient(135deg, #78350f 0%, #92400e 100%)",
            "failed": "linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)",
        }

        status = status_data.get("metadata", {}).get("status", "unknown")
        color = status_colors.get(
            status, "linear-gradient(135deg, #374151 0%, #4b5563 100%)"
        )

        # Determine icon according to status
        status_icons = {
            "completed": "✅",
            "processing": "🔄",
            "pending": "⏳",
            "failed": "❌",
            "unknown": "❓",
        }

        icon = status_icons.get(status, "❓")

        # Additional information
        items = get_complete_queue()
        items_ids = [item.get("id") for item in items]

        position = "-"
        if item_id in items_ids:
            position = f"{items_ids.index(item_id) + 1}"

        metadata = status_data.get("metadata", {})
        print(metadata)
        create = metadata.get("time_start")
        started = metadata.get("time_processing_start")
        ended = metadata.get("time_processing_end")
        detail = metadata.get("detail")

        html_output = f"""
        <div style="background: {color}; 
                    padding: 20px; 
                    border-radius: 12px; 
                    color: #f1f5f9; 
                    font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                    margin: 10px 0;
                    border: 1px solid rgba(148, 163, 184, 0.1);">
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <span style="font-size: 2.5em; margin-right: 15px; filter: brightness(1.2);">{icon}</span>
                <div>
                    <strong style="font-size: 1.5em; text-transform: capitalize; color: #f0f9ff;">{status}</strong>
                    <p style="margin: 8px 0 0 0; color: #cbd5e1; opacity: 0.9;">Item ID: <span style="font-family: monospace; color: #f1f5f9;">{item_id}</span></p>
                </div>
            </div>
            <div style="background: rgba(15, 23, 42, 0.4); padding: 18px; border-radius: 10px; border: 1px solid rgba(148, 163, 184, 0.1);">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <p style="margin: 8px 0; color: #e2e8f0;"><strong style="color: #94a3b8;">🆔 ID:</strong> <span style="color: #f1f5f9; font-family: monospace;">{status_data.get("id", "N/A")}</span></p>
                    <p style="margin: 8px 0; color: #e2e8f0;"><strong style="color: #94a3b8;">📊 Status:</strong> <span style="color: #f1f5f9; text-transform: capitalize;">{status}</span></p>
                    <p style="margin: 8px 0; color: #e2e8f0;"><strong style="color: #94a3b8;">📁 Path:</strong> <span style="color: #f1f5f9; font-family: monospace; font-size: 0.9em;">{status_data.get("path", "N/A")}</span></p>
                    <p style="margin: 8px 0; color: #e2e8f0;"><strong style="color: #94a3b8;">⏰ Create:</strong> <span style="color: #f1f5f9; font-family: monospace;">{create}</span></p>
                    <p style="margin: 8px 0; color: #e2e8f0;"><strong style="color: #94a3b8;">🌐 IP Address:</strong> <span style="color: #f1f5f9; font-family: monospace;">{metadata.get("ip_address", "N/A")}</span></p>
                    {f"<p style='margin: 8px 0; color: #e2e8f0;'><strong style='color: #94a3b8;'>🔄 Processing Start:</strong> <span style='color: #f1f5f9; font-family: monospace;'>{started}</span></p>" if started else ""}
                    {f"<p style='margin: 8px 0; color: #e2e8f0;'><strong style='color: #94a3b8;'>✅ Processing End:</strong> <span style='color: #f1f5f9; font-family: monospace;'>{ended}</span></p>" if ended else ""}
                    {f"<p style='margin: 8px 0; color: #e2e8f0;'><strong style='color: #94a3b8;'>📋 Detail:</strong> <span style='color: #f1f5f9; font-family: monospace;'>{detail}</span></p>" if detail else ""}
                    {f"<p style='margin: 8px 0; color: #e2e8f0;'><strong style='color: #94a3b8;'>📋 Items before:</strong> <span style='color: #f1f5f9; font-family: monospace;'>{position}</span></p>" if position else ""}
                </div>
                {f"<p style='margin: 15px 0 0 0; color: #e2e8f0;'><strong style='color: #94a3b8;'>📋 Results:</strong></p><pre style='background: rgba(0,0,0,0.3); padding: 12px; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; color: #f1f5f9; font-family: monospace; font-size: 0.9em; border: 1px solid rgba(148, 163, 184, 0.1);'>{metadata.get('results', 'No results yet')}</pre>" if metadata.get("results") else ""}
            </div>
        </div>
        """

        # Format complete data for JSON
        formatted_data = {
            "id": status_data.get("id", item_id),
            "path": status_data.get("path", "N/A"),
            "status": status,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat(),
        }

        return formatted_data, html_output

    except Exception as e:
        error_html = f"""
        <div style="background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%); 
                    color: #fef2f2; 
                    padding: 20px; 
                    border-radius: 12px; 
                    font-family: 'Inter', 'Segoe UI', sans-serif;
                    box-shadow: 0 4px 20px rgba(127, 29, 29, 0.2);
                    border: 1px solid rgba(254, 242, 242, 0.1);">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 2em; margin-right: 15px; filter: brightness(1.2);">❌</span>
                <div>
                    <strong style="font-size: 1.3em; color: #fecaca;">Status Check Failed</strong>
                    <p style="margin: 8px 0; color: #fca5a5; opacity: 0.9;">{str(e)}</p>
                </div>
            </div>
        </div>
        """
        return error_html


with gr.Blocks(
    title="Queue Manager Pro",
    theme=gr.themes.Soft(
        primary_hue="slate",
        secondary_hue="gray",
        neutral_hue="gray",
        font=[
            gr.themes.GoogleFont("Inter"),
            "ui-sans-serif",
            "system-ui",
            "sans-serif",
        ],
    ).set(
        background_fill_primary="*neutral_950",
        background_fill_secondary="*neutral_900",
        block_background_fill="*neutral_800",
        block_border_width="1px",
        block_border_color="*neutral_700",
        block_label_background_fill="*neutral_800",
        block_label_border_width="0px",
        block_label_text_color="*neutral_200",
        block_label_text_size="*text_md",
        block_title_text_color="*neutral_100",
        block_title_text_size="*text_lg",
        button_primary_background_fill="*primary_600",
        button_primary_background_fill_hover="*primary_500",
        button_primary_border_color="*primary_500",
        button_primary_text_color="white",
        button_secondary_background_fill="*neutral_700",
        button_secondary_background_fill_hover="*neutral_600",
        button_secondary_border_color="*neutral_600",
        button_secondary_text_color="*neutral_100",
        input_background_fill="*neutral_800",
        input_border_color="*neutral_600",
        input_border_width="1px",
        input_border_color_focus="*primary_500",
        input_placeholder_color="*neutral_400",
        body_background_fill="*neutral_950",
        body_text_color="*neutral_100",
        body_text_color_subdued="*neutral_400",
        color_accent="*primary_500",
        color_accent_soft="*primary_600",
    ),
    css="""
    .gradio-container {
        font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        background: #0f172a !important;
        color: #f1f5f9 !important;
    }
    
    /* Dark mode override for entire app */
    .gradio-container {
        background-color: #0f172a !important;
        color-scheme: dark !important;
    }
    
    /* Tab styling */
    .tab-nav {
        background: #1e293b !important;
        border-radius: 12px !important;
        padding: 8px !important;
        border: 1px solid #334155 !important;
    }
    
    .tab-nav button {
        background: #334155 !important;
        color: #cbd5e1 !important;
        border: none !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
        padding: 12px 24px !important;
    }
    
    .tab-nav button:hover {
        background: #475569 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
    }
    
    .tab-nav button.selected {
        background: #3b82f6 !important;
        color: white !important;
        box-shadow: 0 2px 12px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Form elements */
    .gradio-textbox, .gradio-number {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
    }
    
    .gradio-textbox:focus-within, .gradio-number:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }
    
    /* Buttons */
    .gradio-button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    /* JSON output */
    .gradio-json {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    
    /* Headers and markdown */
    h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e293b;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #64748b;
    }
    
    /* Cards and containers */
    .gradio-block, .gradio-column {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }
    
    /* Labels */
    .gradio-label {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
    }
    """,
) as demo:
    # Main header
    gr.HTML(
        """
    <div style="text-align: center; padding: 30px 0; 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    margin: -20px -20px 20px -20px; border-radius: 0 0 20px 20px;">
        <h1 style="color: white; margin: 0; font-size: 2.5em; font-weight: 300;">
        🚀 Queue Manager Pro</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 1.1em;">
        Advanced Queue Processing System</p>
    </div>
    """
    )

    with gr.Tabs() as tabs:
        # Tab 1: Add to Queue
        with gr.Tab("📤 Add to Queue", elem_classes=["tab-nav"]):
            gr.HTML(
                """
            <div style="text-align: center; padding: 20px; 
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, 
            rgba(147, 51, 234, 0.2) 100%); border-radius: 12px; 
            margin-bottom: 20px; border: 1px solid #334155;">
                <h2 style="color: #f1f5f9; margin: 0;">Add Files to Processing Queue</h2>
                <p style="color: #cbd5e1; margin: 10px 0 0 0;">
                Submit files or directories for background processing</p>
            </div>
            """
            )

            with gr.Row():
                with gr.Column(scale=1):
                    gr.HTML(
                        """
                    <div style="background: #1e293b; padding: 20px; border-radius: 12px; 
                    border-left: 4px solid #3b82f6; border: 1px solid #334155;">
                        <h3 style="color: #f1f5f9; margin-top: 0;">📝 Instructions</h3>
                        <ul style="color: #cbd5e1; line-height: 1.6;">
                            <li>Enter full path to your file or directory</li>
                            <li>Use absolute paths (e.g., /app/data/file.txt)</li>
                            <li>Both files and directories are supported</li>
                            <li>Click "Add to Queue" to start processing</li>
                        </ul>
                    </div>
                    """
                    )

                    input_path = gr.Textbox(
                        label="📁 File/Directory Path",
                        placeholder="Ej: /app/projects/data/raw/file.txt"
                        "or /app/projects/data/raw/",
                        lines=2,
                        max_lines=3,
                        info="Enter the complete path to the file or directory you want to process",
                    )

                    submit_btn = gr.Button(
                        "🚀 Add to Queue",
                        variant="primary",
                        size="lg",
                        elem_classes=["submit-btn"],
                    )

                with gr.Column(scale=1):
                    gr.HTML(
                        """
                    <div style="background: #1e293b; padding: 15px; border-radius: 12px; 
                    margin-bottom: 15px; border: 1px solid #334155;">
                        <h4 style="color: #f1f5f9; margin: 0;">📊 Status Display</h4>
                    </div>
                    """
                    )

                    status_html = gr.HTML(
                        label="📋 Status",
                        value='<div style="text-align: center; padding: 40px; '
                        'color: #cbd5e1; background: #1e293b; '
                        'border-radius: 12px; border: 1px solid #334155;">'
                        '👆 Ready to process your files</div>',
                    )

            submit_btn.click( # pylint: disable=no-member
                fn=add_to_queue,
                inputs=input_path,
                outputs=[status_html],
            )

        # Tab 2: Check Status
        with gr.Tab("📊 Check Status", elem_classes=["tab-nav"]):
            gr.HTML(
                """
            <div style="text-align: center; padding: 20px; background: 
            linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, 
            rgba(5, 150, 105, 0.2) 100%); 
            border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155;">
                <h2 style="color: #f1f5f9; margin: 0;">Check Processing Status</h2>
                <p style="color: #cbd5e1; margin: 10px 0 0 0;">
                Monitor progress of your queued items</p>
            </div>
            """
            )

            with gr.Row():
                with gr.Column(scale=1):
                    gr.HTML(
                        """
                    <div style="background: #1e293b; padding: 20px; border-radius: 12px; 
                    border-left: 4px solid #10b981; border: 1px solid #334155;">
                        <h3 style="color: #f1f5f9; margin-top: 0;">🔍 How to Check Status</h3>
                        <ul style="color: #cbd5e1; line-height: 1.6;">
                            <li>Enter Item ID received when adding to queue</li>
                            <li>The ID is shown in the status display</li>
                            <li>Click "Check Status" to get current progress</li>
                            <li>Status updates include: queued, processing, completed, failed</li>
                        </ul>
                    </div>
                    """
                    )

                    item_id_input = gr.Textbox(
                        label="🆔 Item ID",
                        placeholder="Enter the item ID to check status",
                        info="The ID was provided when you added the item to the queue",
                    )

                    check_status_btn = gr.Button(
                        "🔍 Check Status", variant="secondary", size="lg"
                    )

                with gr.Column(scale=1):
                    gr.HTML(
                        """
                    <div style="background: #1e293b; padding: 15px; border-radius: 12px;
                    margin-bottom: 15px; border: 1px solid #334155;">
                        <h4 style="color: #f1f5f9; margin: 0;">📈 Status Information</h4>
                    </div>
                    """
                    )

                    status_check_html = gr.HTML(
                        label="📊 Status Display",
                        value='<div style="text-align: center; padding: 40px;'
                        'color: #cbd5e1; background: #1e293b;'
                        'border-radius: 12px; border: 1px solid #334155;">'
                        '👆 Enter an Item ID to check status</div>',
                    )

            check_status_btn.click( # pylint: disable=no-member
                fn=get_status,
                inputs=item_id_input,
                outputs=[status_check_html],
            )

    # Footer
    gr.HTML(
        """
    <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 12px;
    margin-top: 20px; border-top: 2px solid #e9ecef;">
        <p style="color: #666; margin: 0;">
            <strong>Queue Manager Pro</strong> | 
            🚀 Powered by Advanced Processing Technology | 
            📊 Real-time Status Monitoring
        </p>
    </div>
    """
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True)
