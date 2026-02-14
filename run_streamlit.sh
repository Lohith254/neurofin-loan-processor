#!/bin/bash
# Neurofin Loan Processor - Streamlit Demo Launcher
# Usage: ./run_streamlit.sh

echo "🚀 Starting Neurofin Loan Processor Demo..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Installing Streamlit..."
    pip install streamlit
fi

# Set environment variables
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_HEADLESS=true

# Launch the app
cd "$(dirname "$0")"
streamlit run app/ui/streamlit_app.py --server.address=0.0.0.0

