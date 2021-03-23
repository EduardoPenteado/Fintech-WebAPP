# FINTECH (WEBAPP)
#### Description:
The Fintech ITO is a tentative of reproducting a webapp which is a fintech. A fintech is a digital bank account.  
  
1. Purpose of the project.
    The purpose of this project is to improve my habilits in building webapps. Also, I enjoy the financial area which is challeging, because of the
high amount of information and the security that you need to provide to your users.  
  
  
2. Programming languages and libraries  
    BackEnd: Python (Librarys: Flask, sqlite3)  
    FrontEnd: Javascript, HTML e CSS (Bootstrap)  


3. How to use?
    First, you will need to run the requirements.txt to install the Flask library  
    pip install -r requirements.txt  

    After installing all the libraries, you must run "flask run" in your shell. The webapp will run in your local server  
    In the directory templates, have all the html templates  
    in the static directory, have all css files and images  
    The other files are python scripts to run the webapp  
        Encrypt.py is a script to encrypt password  
        gen_pass.py is a script to generate and validate credit card  
        helpers.py is a script to add inputs in the database  
        application.py is the main script which contains the flask application  


4. Features
    When you start the application, you'll see a webpage describing a ficticional Fintech called ITO.  

    So, you can open an online banking account, by registering the inputs:  
    *Firstname: Only letters  
    *Secondname: Only letters  
    *ID: ID must be 11 numbers  
    *email: A correct email input  
    *password: must be at least one letter and 8 - 20 length  
    *confirm password: confirm the password writed  
    *phone: A valid phone (internacional)  
  
    When you create an account, your password will be encrypted by the function in the archieve encrypt.py  
    Also, will generate a valid credit card number, a pass code to the card, and a cc number, by the python script in gen_pass.py  
    All these informations here are stored in a database and the password of the credit card is encrypted  
  
    You can see the statement of your account, where is divided by payment, transfer or credit  
    You can pay a bill which is stores in a database  
    You can transfer money of your account to another  
    You can pay your credit debts  
    You can change the email registered of your account  
  
    Other functions like cash and credit where created to test the other funcionalities  
    
    This is a picture of the user interface
    ![alt text](https://github.com/EduardoPenteado/Fintech-WebAPP/blob/main/static/interface.png "Interface")


5. Database
    This is a diagram of the database  
    ![alt text](https://github.com/EduardoPenteado/Fintech-WebAPP/blob/main/static/database.png "Database")
