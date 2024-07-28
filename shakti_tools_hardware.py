import gzip, hashlib, json, os, requests
from lxml import html


def req_sender(url: str, method: str) -> bytes or None:
    # Prepare headers for the HTTP request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }
    # Send HTTP request
    _response = requests.request(method=method, url=url, headers=headers)
    # Check if response is successful
    if _response.status_code != 200:
        print(f"HTTP Status code: {_response.status_code}")  # Print status code if not 200
        return None
    return _response  # Return the response if successful


def ensure_dir_exists(path: str):
    # Check if directory exists, if not, create it
    if not os.path.exists(path):
        os.makedirs(path)
        print(f'Directory {path} Created')  # Print confirmation of directory creation


def page_checker(url: str, method: str, directory_path: str):
    # Create a unique hash for the URL to use as the filename
    page_hash = hashlib.sha256(string=url.encode(encoding='UTF-8', errors='backslashreplace')).hexdigest()
    ensure_dir_exists(path=directory_path)  # Ensure the directory exists
    file_path = os.path.join(directory_path, f"{page_hash}.html.gz")  # Define file path
    if os.path.exists(file_path):  # Check if the file already exists
        print("File exists, reading it...")  # Notify that the file is being read
        print(f"Filename is {page_hash}")
        with gzip.open(filename=file_path, mode='rb') as file:
            file_text = file.read().decode(encoding='UTF-8', errors='backslashreplace')  # Read and decode file
        return file_text  # Return the content of the file
    else:
        print("File does not exist, Sending request & creating it...")  # Notify that a request will be sent
        _response = req_sender(url=url, method=method)  # Send the HTTP request
        if _response is not None:
            print(f"Filename is {page_hash}")
            with gzip.open(filename=file_path, mode='wb') as file:
                if isinstance(_response, str):
                    file.write(_response.encode())  # Write response if it is a string
                    return _response
                file.write(_response.content)  # Write response content if it is bytes
            return _response.text  # Return the response text


def scrape_func(url: str, method: str, path: str):
    # Get HTTP response text
    html_response_text = page_checker(url=url, method=method, directory_path=path)
    # Parse HTML content using lxml
    parsed_html = html.fromstring(html=html_response_text)

    # Define XPath to extract category IDs
    xpath_categories_id = "//span[contains(@class , 'CategoryItem-sc-12a69d60-2')]/@id"
    categories_id_list = [category_id[9:] for category_id in parsed_html.xpath(xpath_categories_id)]  # Extract IDs
    xpath_categories_name = "//span[contains(@class , 'CategoryItem-sc-12a69d60-2')]//text()"
    categories_name_list = [category_name for category_name in
                            parsed_html.xpath(xpath_categories_name)]  # Extract Names
    cat_ids_names = [(cat_id, cat_name) for cat_id, cat_name in zip(categories_id_list, categories_name_list)]
    print(cat_ids_names)
    final_output = []  # Initialize final output list
    for cat in cat_ids_names:
        base_link = ('https://api.dotshowroom.in/api/dotk/catalog/getItemsBasicDetails/1015404?category_id=C-I-D'
                     '&category_typ0&page_no=1')
        page_1_link = base_link.replace('C-I-D', cat[0])  # Replace placeholder with actual category ID
        this_category_products = {}  # Initialize dictionary for this category
        this_page_products = []  # Initialize list for products on this page
        page_counter = 1  # Initialize page counter
        is_next_page = True  # Flag to check if more pages exist
        while is_next_page:
            next_page_link = page_1_link.replace('=1', '=' + str(page_counter))  # Update page number in URL
            api_response = page_checker(url=next_page_link, method=method, directory_path=os.path.join(project_files_dir, 'Category_Pages'))
            api_text = json.loads(api_response)  # Load JSON response
            product_list = api_text.get('items')  # Get list of products

            for each_product in product_list:  # Iterate over each product
                this_product = {
                    "Name": each_product.get("name"),
                    "Price": each_product.get("price"),
                    "Discounted Price": each_product.get("discounted_price") if each_product.get("discounted_price") != each_product.get("price") else None,
                    "Link": each_product.get("link")
                }
                this_page_products.append(this_product)  # Add product details to list
            is_next_page = api_text.get('next_page')  # Check if there is a next page
            page_counter += 1  # Increment page counter
        this_category_products[cat[1]] = this_page_products  # Add products to category dictionary
        final_output.append(this_category_products)  # Add category dictionary to final output

    with open('new_final_output.json', 'w') as file:
        file.write(json.dumps(final_output, indent=4))  # Write final output to JSON file


# Define main URL, method, and path
my_url = "https://shaktitoolsandhardwarestore.com/"
my_method = "GET"

# Creating Saved Pages Directory for this Project if not Exists
project_name = 'Shakti_Tools'

project_files_dir = f'C:\\Project Files\\{project_name}_Project_Files'
ensure_dir_exists(path=project_files_dir)

# Call the scraping function with specified parameters
scrape_func(url=my_url, method=my_method, path=os.path.join(project_files_dir, 'Main_Page'))
