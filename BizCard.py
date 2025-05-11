import streamlit as st 
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import psycopg2
# set STREAMLIT_WATCH_USE_POLLING=true 

# streamlit run BizCard.py 


def image_to_text(path):
    # Load the image
    input_Image = Image.open(path)
    
    # Converting image to array format
    image_Array = np.array(input_Image)

    # Instantiate the Reader object
    reader = easyocr.Reader(['en'])

    # Extract text from the image
    result = reader.readtext(image_Array)

    # Process the result
    text = [entry[1] for entry in result]
    
    return text, input_Image


def extract_text(text):
    extract_dict = {
        'NAME': [], 'DESIGNATION': [], 'COMPANY NAME': [],
        'CONTACT': [], 'EMAIL': [], 'WEBSITE': [],
        'ADDRESS': [], 'PINCODE': []
    }

    # Extract Name and Designation
    extract_dict['NAME'].append(text[0])
    extract_dict['DESIGNATION'].append(text[1])
    
    # Process remaining text
    for i in range(2, len(text)):
        
        # Capture all phone numbers (even if there are multiple)
        if text[i].startswith('+') or (text[i].replace('-', '').isdigit() and '-' in text[i]):
            extract_dict['CONTACT'].append(text[i])
        
        # Capture email with .com
        elif '@' in text[i] and '.com' in text[i]:
            extract_dict['EMAIL'].append(text[i])
        
        # Capture website (any format with www or .com)
        elif 'www' in text[i].lower() or '.com' in text[i].lower():
            small = text[i].lower()
            extract_dict['WEBSITE'].append(small)
        
        # Capture Pincode (6 digits only)
        elif re.search(r'\b\d{6}\b', text[i]):
            extract_dict['PINCODE'].append(text[i])
        
        # Capture Company Name (if it is single word or uppercase)
        elif text[i].isupper() and len(text[i]) > 2:
            extract_dict['COMPANY NAME'].append(text[i])
        
        # Capture Address (ignore unwanted text like "digitals", "INSURANCE")
        elif len(text[i].split()) > 2:  # If sentence length > 2, it's an address
            remove_colon = re.sub(r'[,;]', '', text[i])
            extract_dict['ADDRESS'].append(remove_colon)
        
        # Ignore any garbage text like "digitals", "INSURANCE", "St ,"
        else:
            continue
    
    # Concatenate and Clean All Values
    for key, value in extract_dict.items():
        if len(value) > 0:
            concatenated = ', '.join(value)
            extract_dict[key] = [concatenated]
        else:
            extract_dict[key] = ['NA']
    
    return extract_dict


# Streamlit part
st.set_page_config(layout="wide", initial_sidebar_state="expanded")
st.title(':violet[Bizcardx Extracting Business Card Data with OCR]')
with st.sidebar:
    selected = option_menu(
        'Main Menu',
        ['Home', 'Upload & Modify', 'Delete'],
        icons=['house', 'cloud-upload', 'trash'],
        menu_icon="cast",  # Sidebar icon
        default_index=0,
        orientation='vertical',
        styles={
            "container": {"padding": "5px", "background-color": "#F2EFD6"},
            "icon": {"color": "#cc3366", "font-size": "20px"},
            "nav-link": {
                "font-size": "18px",
                "color": "#2C3E50",
                "padding": "10px",
                "border-radius": "5px"
            },
            "nav-link-selected": {
                "background-color": "#1ABC9C",
                "color": "white",
                "font-weight": "bold"
            },
        }
    )

    
if selected == 'Home':

        if selected == 'Home':

            st.subheader("**:blue[Technologies Used:]** :green[Python, easyOCR, Streamlit, PostgreSQL, Pandas]")

            st.markdown("""
    <p style='color:black'>
    This Streamlit web application allows you to upload an image of a business card and use EasyOCR to extract the necessary information from it. 
    In this program, the extracted data can be viewed, changed, or removed. Additionally, users of this software would be able to upload a photo 
    of their business card and save the extracted data with it to a database. Each entry would have its own business card image and extracted data, 
    and the database would be able to store many entries.
    </p>
    """, unsafe_allow_html=True)

            st.write(":red[Note:]:orange[ Only business cards are permitted to be used.]")


if selected == 'Upload & Modify':
    Upload_card = st.file_uploader(':red[Upload here]', type=['png', 'jpg', 'jpeg'])
    
    if Upload_card is not None:
        st.image(Upload_card, width=500, caption="Uploaded Business Card")
        
        text, input_Image = image_to_text(Upload_card)
        extract_dict = extract_text(text)
        
        if extract_dict :
            st.success('TEXT IS EXTRACTED SUCCESSFULLY')
            
        df_1 = pd.DataFrame(extract_dict)
        
        # Covert image to byte
        image_To_Bytes = io.BytesIO()
        input_Image.save(image_To_Bytes, format= 'PNG')
        image_Data = image_To_Bytes.getvalue()
        
        # Creating dictionary 
        data = {'IMAGE' : [image_Data]}
        df_2 = pd.DataFrame(data)
        concat_df = pd.concat([df_1, df_2], axis= 1)
        st.dataframe(concat_df)
        
        
        # Button_save = st.button('Save')
        st.markdown("<style>div.stButton > button {background-color: #4CAF50; color: black; font-size: 18px; padding: 0.75em 2em;}</style>", unsafe_allow_html=True); Button_save = st.button('Save')
        if Button_save:
            # Connecting to PostgreSQL
            postgres_Connection = psycopg2.connect(user="postgres",
                                                    password="sudhakar",
                                                    host="localhost",
                                                    port= 5432,
                                                    database="bizxcard_data")
            postgres_Cursor = postgres_Connection.cursor()

            # Table creation
            create_table_query = '''CREATE TABLE IF NOT EXISTS Bizcard_info (Name VARCHAR(100),
                                                                                Designation VARCHAR(50),
                                                                                Company_name VARCHAR(50),
                                                                                Contact VARCHAR(50),
                                                                                Email VARCHAR(50),
                                                                                Website TEXT,
                                                                                Address TEXT,
                                                                                pin_code VARCHAR(50),
                                                                                Image text ) '''
            postgres_Cursor.execute(create_table_query)
            postgres_Connection.commit()
            
            # insert query
            Insert_table_query = '''INSERT INTO Bizcard_info(Name, Designation, Company_name, Contact, Email, Website, Address, pin_code, Image)
                                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                                                            
            Data = concat_df.values.tolist()[0]
            try:
                postgres_Cursor.execute(Insert_table_query, Data)
                postgres_Connection.commit()
            except Exception as e:
                print("An error occurred:", e)
                postgres_Connection.rollback()  # Rollback the transaction
            st.success('DATA SAVED SUCCESFULLY')
        
        
    Method = st.radio(':red[Select the method]', ['None','Preview', 'Modify'])
    if Method == 'None':
        pass
    elif Method == 'Preview':
        # Connecting to PostgreSQL
        postgres_Connection = psycopg2.connect(user="postgres",
                                                password="sudhakar",
                                                host="localhost",
                                                port= 5432,
                                                database="bizxcard_data")
        postgres_Cursor = postgres_Connection.cursor()
        # Select Query
        Select_table_query = 'select * from Bizcard_info'
        postgres_Cursor.execute(Select_table_query)
        Table_1 = postgres_Cursor.fetchall()
        Table_Df_1 = pd.DataFrame(Table_1, columns=('Name', 'Designation', 'Company_name', 'Contact', 'Email', 'Website', 'Address', 'pin_code', 'Image'))
        st.dataframe(Table_Df_1)
        
    elif Method == 'Modify':
        # Connecting to PostgreSQL
        postgres_Connection = psycopg2.connect(user="postgres",
                                                password="sudhakar",
                                                host="localhost",
                                                port= 5432,
                                                database="bizxcard_data")
        postgres_Cursor = postgres_Connection.cursor()
        
        # Select Query
        Select_table_query_2 = 'select * from Bizcard_info'
        postgres_Cursor.execute(Select_table_query_2)
        Table_2 = postgres_Cursor.fetchall()
        Table_Df_2 = pd.DataFrame(Table_2, columns=('Name', 'Designation', 'Company_name', 'Contact', 'Email', 'Website', 'Address', 'pin_code', 'Image'))
        
        column1, column2 = st.columns(2)
        with column1:
            selected_Name = st.selectbox('Select the name', Table_Df_2['Name'])
        Df_2 = Table_Df_2[Table_Df_2['Name'] == selected_Name]
        # st.dataframe(Df_2)
        
        Df_2_1 = Df_2.copy()
        
        column1, column2 = st.columns(2)
        with column1:
            Modify_Name = st.text_input('Name', Df_2['Name'].unique()[0])
            Modify_Designation = st.text_input('Designation', Df_2['Designation'].unique()[0])
            Modify_Company_name = st.text_input('Company_name', Df_2['Company_name'].unique()[0])
            Modify_Contact = st.text_input('Contact', Df_2['Contact'].unique()[0])
            Modify_Email = st.text_input('Email', Df_2['Email'].unique()[0])
            
            Df_2_1['Name'] = Modify_Name
            Df_2_1['Designation'] = Modify_Designation
            Df_2_1['Company_name'] = Modify_Company_name
            Df_2_1['Contact'] = Modify_Contact
            Df_2_1['Email'] = Modify_Email
            
        with column2 :
            Modify_Website = st.text_input('Website', Df_2['Website'].unique()[0])
            Modify_Address = st.text_input('Address', Df_2['Address'].unique()[0])
            Modify_pin_code = st.text_input('pin_code', Df_2['pin_code'].unique()[0])
            Modify_Image = st.text_input('Image', Df_2['Image'].unique()[0])
             
            Df_2_1['Website'] = Modify_Website
            Df_2_1['Address'] = Modify_Address
            Df_2_1['pin_code'] = Modify_pin_code
            Df_2_1['Image'] = Modify_Image

        st.dataframe(Df_2_1)
        
        column1, column2 = st.columns(2)
        with column1:
            
            Modify_Button = st.button('MODIFY', use_container_width= True)

        if Modify_Button :
            # Connecting to PostgreSQL
            postgres_Connection = psycopg2.connect(user="postgres",
                                                    password="sudhakar",
                                                    host="localhost",
                                                    port= 5432,
                                                    database="bizxcard_data")
            postgres_Cursor = postgres_Connection.cursor()
            
            postgres_Cursor.execute(f"Delete from Bizcard_info where Name = '{selected_Name}' ")
            postgres_Connection.commit()
            
            # insert query
            Insert_table_query = '''INSERT INTO Bizcard_info(Name, Designation, Company_name, Contact, Email, Website, Address, pin_code, Image)
                                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                                                            
            Data = Df_2_1.values.tolist()[0]
            try:
                postgres_Cursor.execute(Insert_table_query, Data)
                postgres_Connection.commit()
            except Exception as e:
                print("An error occurred:", e)
                postgres_Connection.rollback()  # Rollback the transaction
            st.success('DATA MODIFIED SUCCESFULLY')
            
            
if selected == 'Delete':
    # Connecting to PostgreSQL
    postgres_Connection = psycopg2.connect(user="postgres",
                                            password="sudhakar",
                                            host="localhost",
                                            port= 5432,
                                            database="bizxcard_data")
    postgres_Cursor = postgres_Connection.cursor()
    
    column1, column2 = st.columns(2)
    with column1 :
        # Select Query
        Select_table_query = 'select Name from Bizcard_info'
        postgres_Cursor.execute(Select_table_query)
        Table_1 = postgres_Cursor.fetchall()

        Names = []
        for i in Table_1 :
            Names.append(i[0])
        
        Name_select = st.selectbox('Select the name', Names)
        
        
    with column2 :
        # Select Query
        Select_table_query = f"select Designation from Bizcard_info where Name = '{Name_select}' "
        postgres_Cursor.execute(Select_table_query)
        Table_2 = postgres_Cursor.fetchall()

        Designation = []
        for j in Table_2 :
            Designation.append(j[0])
        
        Designation_select = st.selectbox('Select the Designation', Designation)
        
    
    if Name_select and Designation_select :

        st.write(f"Selected Name : '{Name_select}' ")
        st.write(f"Designation Name : '{Designation_select}' ")

        # Delete_button = st.button(':blue[Delete]')   
        st.markdown("<style>div.stButton > button {background-color: #f44336; color: white; font-size: 18px; padding: 0.75em 2em; border-radius: 8px;}</style>", unsafe_allow_html=True); Delete_button = st.button('Delete')
        
        if Delete_button :
            postgres_Cursor.execute(f"Delete from Bizcard_info where Name = '{Name_select}' and Designation = '{Designation_select}' ")
            postgres_Connection.commit()
            
            st.warning("DELETED SUCCESSFULLY")
