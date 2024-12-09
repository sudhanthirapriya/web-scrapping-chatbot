# Python Project

## Prerequisites
- Latest version of Python
- Latest version of pip

## API Keys
You will need to obtain API keys from the following services:

- **Gemini:** [Get your Gemini API keys here](https://gemini.google.com/app)
- **Llama/Groq:** [Get your Groq API keys here](https://console.groq.com/keys)

### Update .env File
Make sure to update your `.env` file with the API keys:

```sh
GOOGLE_API_KEY= 
GROQ_API_KEY=
```

## Setting Up Your Environment

1. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   ```
2. **Activate the Virtual Environment:**
- On Windows
   ```bash
   venv\Scripts\activate
   ```
- On Linux
    ```bash
    source venv/bin/activate
    ```
3. **Install Required Packages:**
   ```bash
    pip install -r requirements.txt
    ```

## Training the Model
```bash
python scrap_n_train.py
```
- You will need to provide:
1. The sitemap URL.
2. The name of the store.

## Running the Project
```bash
streamlit run server.py
```
