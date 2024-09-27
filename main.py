import streamlit as st
import cv2
import pandas as pd
import datetime
import os
import numpy as np

# Function to update attendance in a local CSV file
def update_attendance(file_path, name, email):
    try:
        df = pd.read_csv(file_path)
        
        # Check if the name and email exist in the DataFrame
        for index, record in df.iterrows():
            if record['Name'] == name and record['Email Address'] == email:  # Ensure column names match
                if record['Attendance'] == 'present':  # Check if already marked present
                    return False, None  # Don't update if already present
                
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                df.at[index, 'Attendance'] = 'present'  # Update attendance to 'present'
                df.at[index, 'Time'] = current_time  # Update the time
                df.to_csv(file_path, index=False)  # Save the updated DataFrame
                return True, current_time
                
        return False, None  # Return false if no matching record is found
    except Exception as e:
        st.error(f"Error updating attendance: {e}")
        return False, None

# Function to decode QR code from an image or frame
def decode_qr_code(frame):
    detector = cv2.QRCodeDetector()
    data, vertices_array, binary_qrcode = detector.detectAndDecode(frame)
    return data

def display_attendance_records(file_path):
    try:
        df = pd.read_csv(file_path)
        present_records = df[df['Attendance'] == 'present'][['Email Address', 'Name', 'Attendance', 'Time']]
        
        if not present_records.empty:
            st.write("### Present Attendance Records")
            st.dataframe(present_records)
        else:
            st.write("No records of present attendance found.")
    except Exception as e:
        st.error(f"Error reading attendance records: {e}")

def scan_qr_code(file_path):
    st.title("QR Code Scanner")
    st.write("Click the button below to start the camera and scan a QR code.")

    # Initialize session state for control buttons and decoded message
    if "scanning" not in st.session_state:
        st.session_state.scanning = False

    if "decoded_message" not in st.session_state:
        st.session_state.decoded_message = None

    # Add fields to store attendance details
    if "attendance_details" not in st.session_state:
        st.session_state.attendance_details = None

    def start_scanning():
        st.session_state.scanning = True
        st.session_state.decoded_message = None  # Reset the decoded message when starting
        st.session_state.attendance_details = None  # Reset attendance details

    def stop_scanning():
        st.session_state.scanning = False

    if not st.session_state.scanning:
        if st.button('Start Scanning', key='start'):
            start_scanning()

    if st.session_state.scanning:
        st.write("Camera is active. Scan the QR code.")
        
        # Use Streamlit's camera input
        frame = st.camera_input("Capture a QR Code", key="camera")

        if frame is not None:
            # Read the image data from the UploadedFile object
            img_bytes = frame.read()  # Read the bytes from the UploadedFile

            # Convert the image from bytes to a format OpenCV can read
            img_array = np.frombuffer(img_bytes, np.uint8)  # Convert bytes to a NumPy array
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            # Ensure the image is valid
            if img is not None:
                qr_code = decode_qr_code(img)
                if qr_code:
                    if st.session_state.decoded_message != qr_code:
                        st.session_state.decoded_message = qr_code
                        st.success(f"Decoded QR Code: {qr_code}")

                        # Split the decoded data to get name and email
                        if ', ' in qr_code:
                            name, email = qr_code.split(", ")
                            # Update attendance in local CSV file
                            success, time = update_attendance(file_path, name, email)
                            if success:
                                attendance_info = f"**Name:** {name}\n**Email:** {email}\n**Attendance:** present\n**Time:** {time}"
                                st.session_state.attendance_details = attendance_info
                                st.success(f"Attendance updated for {name} at {time}.")
                            else:
                                st.warning(f"No record found for {name} in the CSV or attendance already marked as present.")
                        
                        # Automatically stop scanning after processing the QR code
                        stop_scanning()
                else:
                    st.error("No QR code detected. Please try again.")
            else:
                st.error("Captured frame is not valid. Please try again.")

        # Display attendance details if available
        if st.session_state.attendance_details:
            st.markdown(st.session_state.attendance_details)

        # Option to stop scanning manually
        if st.button('Stop Scanning', key='stop', on_click=stop_scanning):
            stop_scanning()


def main():
    st.title("AWS Student Community Day Attendance System")
    # Specify the path to your local CSV file
    file_path = "attendance.csv"
    # Check if the file exists
    if file_path and os.path.exists(file_path):
        st.success("CSV file found. You can now upload a QR code image or scan one.")

        # Option to upload an image with QR code
        uploaded_file = st.file_uploader("Upload an Image with QR Code", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            # Save the uploaded file temporarily
            with open("uploaded_qr.png", "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Decode the QR Code
            data = decode_qr_code(cv2.imread("uploaded_qr.png"))
            if data:
                if ', ' in data:
                    name, email = data.split(", ")
                    st.success(f"Decoded Data:\n**Name:** {name}\n**Email:** {email}")

                    # Update attendance in local CSV file
                    success, time = update_attendance(file_path, name, email)
                    if success:
                        st.success(f"Attendance updated for {name} at {time}.")
                    else:
                        st.warning(f"No record found for {name} in the CSV or attendance already marked as present.")
                else:
                    st.error("Invalid QR code format. Please ensure it contains 'Name, Email'.")
            else:
                st.error("No QR code detected or QR code is invalid. Please try another image.")

        # Start QR code scanning
        scan_qr_code(file_path)
    else:
        if file_path:
            st.error("CSV file not found. Please check the path.")
    display_attendance_records(file_path)

if __name__ == "__main__":
    main()
