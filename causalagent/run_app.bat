@echo off
echo Starting Causal Agent Streamlit App...
echo.
echo Make sure you have set your OPENAI_API_KEY environment variable!
echo.
python -m streamlit run app.py --server.port 8501 --server.address localhost
pause 