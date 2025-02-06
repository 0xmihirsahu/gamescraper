
The script will:
1. Launch a browser instance
2. Navigate to PlayToEarn.com's blockchain games page
3. Extract game information from the table
4. Save the results to `table_content.html`

## Output

The script generates a `table_content.html` file containing the extracted game information from the third column of the games table.

## To run this project

1. Install Playwright:

```bash
pip install playwright
playwright install # Install browser dependencies
```

2. Run the script:

```bash
python script.py
```

## Features

- Headless browser automation using Playwright
- Asynchronous execution for better performance
- Handles dynamic content loading
- User-agent spoofing to avoid blocking
- Error handling for network issues

## Contributing

Feel free to fork this repository and submit pull requests for any improvements.

## License

[MIT License](LICENSE)