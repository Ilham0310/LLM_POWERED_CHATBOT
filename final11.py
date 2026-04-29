import streamlit as st
import pymysql
from datetime import datetime
import json
from groq import Groq
import os
import numpy as np
import tensorflow as tf
from PIL import Image
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# API Keys and Environment Setup
GROQ_API_KEY = 'gYOUR_GROQ_API_KEY'  # Replace with your actual Groq API key
os.environ["GROQ_API_KEY"] = GROQ_API_KEY
GOOGLE_API_KEY = 'YOUR_GOOGLE_API_KEY'  # Replace with your actual Google API key
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="Llama3-8b-8192")
schema = """
                -- Patients Table
                CREATE TABLE IF NOT EXISTS Patients (
                    PatientID INT PRIMARY KEY AUTO_INCREMENT,
                    FirstName VARCHAR(50),
                    LastName VARCHAR(50),
                    Age INT,
                    Gender CHAR(1),
                    ContactNumber VARCHAR(15),
                    Address VARCHAR(100)
                );

                -- Doctors Table
                CREATE TABLE IF NOT EXISTS Doctors (
                    DoctorID INT PRIMARY KEY AUTO_INCREMENT,
                    FirstName VARCHAR(50),
                    LastName VARCHAR(50),
                    Specialty VARCHAR(50),
                    ContactNumber VARCHAR(15),
                    DepartmentID INT
                );

                -- Departments Table
                CREATE TABLE IF NOT EXISTS Departments (
                    DepartmentID INT PRIMARY KEY AUTO_INCREMENT,
                    DepartmentName VARCHAR(50),
                    Floor INT
                );

                -- Appointments Table
                CREATE TABLE IF NOT EXISTS Appointments (
                    AppointmentID INT PRIMARY KEY AUTO_INCREMENT,
                    PatientID INT,
                    DoctorID INT,
                    Date DATE,
                    Time TIME,  -- TIME column fixed to match correct SQL format
                    Reason VARCHAR(100),
                    FOREIGN KEY (PatientID) REFERENCES Patients(PatientID),
                    FOREIGN KEY (DoctorID) REFERENCES Doctors(DoctorID)
                );

                -- MedicalRecords Table
                CREATE TABLE IF NOT EXISTS MedicalRecords (
                    RecordID INT PRIMARY KEY AUTO_INCREMENT,
                    PatientID INT,
                    DoctorID INT,
                    Diagnosis VARCHAR(100),
                    Treatment VARCHAR(100),
                    Date DATE,
                    FOREIGN KEY (PatientID) REFERENCES Patients(PatientID),
                    FOREIGN KEY (DoctorID) REFERENCES Doctors(DoctorID)
                );

                -- Users Table
                CREATE TABLE IF NOT EXISTS Users (
                    user_id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,  -- Store hashed passwords
                    role ENUM('patient', 'doctor', 'admin') NOT NULL,
                    PatientID INT NULL,  -- Foreign key referencing Patients table
                    DoctorID INT NULL,   -- Foreign key referencing Doctors table
                    FOREIGN KEY (PatientID) REFERENCES Patients(PatientID),
                    FOREIGN KEY (DoctorID) REFERENCES Doctors(DoctorID)
                );
                """

# Database Connection
def get_db_connection():
    try:
        connection = pymysql.connect(
            host='YOUR_HOSTt',
            user='YOUR_DATABASE_USER',
            password='YOUR_DATABASE_PASSWORD',
            database='YOUR_DATABASE_NAME',
        )
        return connection
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return None

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'user' not in st.session_state:
    st.session_state['user'] = None

def login(username, password):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                query = "SELECT * FROM Users WHERE username = %s AND password = %s"
                cursor.execute(query, (username, password))
                user = cursor.fetchone()
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = user
                    return True
                return False
        finally:
            connection.close()
    return False

def logout():
    st.session_state['logged_in'] = False
    st.session_state['user'] = None
    st.rerun()

def view_patient_details(patient_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Patients WHERE PatientID = %s", (patient_id,))
                patient = cursor.fetchone()
                if patient:
                    st.header("My Details")
                    st.write(f"*Name:* {patient[1]} {patient[2]}")
                    st.write(f"*Age:* {patient[3]}")
                    st.write(f"*Gender:* {patient[4]}")
                    st.write(f"*Contact:* {patient[5]}")
                    st.write(f"*Address:* {patient[6]}")
                else:
                    st.error("Patient details not found.")
        finally:
            connection.close()

def view_patient_appointments(patient_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT a.AppointmentID, d.FirstName, d.LastName, a.Date, a.Time, a.Reason 
                    FROM Appointments a
                    JOIN Doctors d ON a.DoctorID = d.DoctorID
                    WHERE a.PatientID = %s
                    ORDER BY a.Date, a.Time
                """, (patient_id,))
                appointments = cursor.fetchall()
                
                st.header("My Appointments")
                if appointments:
                    for appt in appointments:
                        with st.expander(f"Appointment with Dr. {appt[1]} {appt[2]} on {appt[3]}"):
                            st.write(f"*Time:* {appt[4]}")
                            st.write(f"*Reason:* {appt[5]}")
                else:
                    st.info("No appointments scheduled.")
        finally:
            connection.close()

def view_patient_medical_records(patient_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT mr.RecordID, d.FirstName, d.LastName, mr.Diagnosis, mr.Treatment, mr.Date
                    FROM MedicalRecords mr
                    JOIN Doctors d ON mr.DoctorID = d.DoctorID
                    WHERE mr.PatientID = %s
                    ORDER BY mr.Date DESC
                """, (patient_id,))
                records = cursor.fetchall()
                
                st.header("My Medical Records")
                if records:
                    for record in records:
                        with st.expander(f"Medical Record from Dr. {record[1]} {record[2]} on {record[5]}"):
                            st.write(f"*Diagnosis:* {record[3]}")
                            st.write(f"*Treatment:* {record[4]}")
                else:
                    st.info("No medical records found.")
        finally:
            connection.close()

def book_new_appointment(patient_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Retrieve available doctors
                cursor.execute("SELECT DoctorID, FirstName, LastName, Specialty FROM Doctors")
                doctors = cursor.fetchall()
                doctor_options = {f"Dr. {d[1]} {d[2]} ({d[3]})": d[0] for d in doctors}
                
                st.header("Book New Appointment")
                with st.form("appointment_form"):
                    doctor = st.selectbox("Select Doctor", options=list(doctor_options.keys()))
                    date = st.date_input("Date", min_value=datetime.now().date())
                    time = st.time_input("Time")
                    reason = st.text_area("Reason for Appointment")
                    
                    if st.form_submit_button("Book Appointment"):
                        doctor_id = doctor_options[doctor]
                        appointment_time = time.strftime('%H:%M:%S')
                        
                        # Check if an appointment already exists with the same details
                        cursor.execute("""
                            SELECT * FROM Appointments 
                            WHERE PatientID = %s AND DoctorID = %s AND Date = %s AND Time = %s
                        """, (patient_id, doctor_id, date, appointment_time))
                        existing = cursor.fetchone()
                        
                        if existing:
                            st.info("This appointment is already booked.")
                        else:
                            cursor.execute("""
                                INSERT INTO Appointments (PatientID, DoctorID, Date, Time, Reason)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (patient_id, doctor_id, date, appointment_time, reason))
                            connection.commit()
                            st.success("Appointment booked successfully!")
        finally:
            connection.close()

def admin_chatbot():
    st.header("Admin Chatbot")
    query = st.text_input("Enter your query:")
    if st.button("Submit"):
        prompt = ChatPromptTemplate.from_template(f"""
                    Here is the schema for a database:
                    {schema}
                    Based on this scheme, write the SQL query to achieve the following:
                    {query}
                    Please provide a response to the following question based on your general knowledge.
                    Give only the SQL query as output and nothing else. Query should be simple and effective.  
                """)
        try:
            messages = prompt.format_messages(input=prompt)
            response = llm.invoke(messages)
            generated_query = response.content

            # Preprocess the generated query
            # Remove triple quotes and strip whitespace
            generated_query = generated_query.replace('```', '').strip()

            # Display the generated SQL query
            st.write("Generated SQL Query:")
            st.code(generated_query)

            # Execute the query and handle results
            connection = get_db_connection()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(generated_query)

                        # Check if the query is a SELECT query
                        if generated_query.strip().lower().startswith("select"):
                            results = cursor.fetchall()
                            if results:
                                st.write("Query Results:")
                                st.table(results)
                            else:
                                st.info("No results returned from the query.")
                        else:
                            # For INSERT, UPDATE, DELETE queries, commit the transaction
                            connection.commit()
                            st.success("Query executed successfully!")
                except Exception as e:
                    st.error(f"Error executing query: {str(e)}")
                finally:
                    connection.close()
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")

def main():
    if not st.session_state['logged_in']:
        st.title("Hospital Management System")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if login(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    else:
        # Add logout button
        st.sidebar.button("Logout", on_click=logout)
        
        user = st.session_state['user']
        user_dict = {
            'user_id': user[0],
            'username': user[1],
            'password': user[2],
            'role': user[3],
            'PatientID': user[4],
            'DoctorID': user[5]
        }

        st.title(f"Welcome, {user_dict['username']} ({user_dict['role'].capitalize()})")

        if user_dict['role'] == 'doctor':
            doctor_id = user_dict['DoctorID']
            
            # Create tabs for different functionalities
            tabs = st.tabs(["My Details", "Appointments", "Add Medical Record"])
            
            with tabs[0]:
                view_doctor_details(doctor_id)
                
            with tabs[1]:
                view_doctor_appointments(doctor_id)
                
            with tabs[2]:
                add_medical_record(doctor_id)

        elif user_dict['role'] == 'patient':
            patient_id = user_dict['PatientID']
            
            # Create tabs for different functionalities
            tabs = st.tabs(["My Details", "Appointments", "Medical Records", "Book Appointment"])
            
            with tabs[0]:
                view_patient_details(patient_id)
                
            with tabs[1]:
                view_patient_appointments(patient_id)
                
            with tabs[2]:
                view_patient_medical_records(patient_id)
                
            with tabs[3]:
                book_new_appointment(patient_id)

        elif user_dict['role'] == 'admin':
            # Create tabs for different functionalities
            tabs = st.tabs(["Admin Chatbot"])
            
            with tabs[0]:
                admin_chatbot()

def view_doctor_details(doctor_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Doctors WHERE DoctorID = %s", (doctor_id,))
                doctor = cursor.fetchone()
                if doctor:
                    st.header("My Details")
                    st.write(f"*Name:* {doctor[1]} {doctor[2]}")
                    st.write(f"*Specialty:* {doctor[3]}")
                    st.write(f"*Contact:* {doctor[4]}")
                else:
                    st.error("Doctor details not found.")
        finally:
            connection.close()

def view_doctor_appointments(doctor_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT a.AppointmentID, p.FirstName, p.LastName, a.Date, a.Time, a.Reason 
                    FROM Appointments a
                    JOIN Patients p ON a.PatientID = p.PatientID
                    WHERE a.DoctorID = %s
                    ORDER BY a.Date, a.Time
                """, (doctor_id,))
                appointments = cursor.fetchall()
                
                st.header("My Appointments")
                if appointments:
                    for appt in appointments:
                        with st.expander(f"Appointment with {appt[1]} {appt[2]} on {appt[3]}"):
                            st.write(f"*Time:* {appt[4]}")
                            st.write(f"*Reason:* {appt[5]}")
                else:
                    st.info("No appointments scheduled.")
        finally:
            connection.close()

def add_medical_record(doctor_id):
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT PatientID, FirstName, LastName FROM Patients")
                patients = cursor.fetchall()
                patient_options = {f"{p[1]} {p[2]}": p[0] for p in patients}
                
                st.header("Add Medical Record")
                with st.form("medical_record_form"):
                    patient = st.selectbox("Select Patient", options=list(patient_options.keys()))
                    diagnosis = st.text_area("Diagnosis")
                    treatment = st.text_area("Treatment")
                    date = st.date_input("Date", datetime.now())
                    
                    if st.form_submit_button("Submit"):
                        patient_id = patient_options[patient]
                        cursor.execute("""
                            INSERT INTO MedicalRecords (PatientID, DoctorID, Diagnosis, Treatment, Date)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (patient_id, doctor_id, diagnosis, treatment, date))
                        connection.commit()
                        st.success("Medical record added successfully!")
        finally:
            connection.close()

if __name__ == "__main__":
    main()