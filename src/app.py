import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from PIL import Image
import io
import base64
from pymongo import MongoClient
from bson.objectid import ObjectId
import pandas as pd

# Create a MongoDB connection and cache it
@st.cache_resource
def get_mongo_client(uri):
    """Create a MongoDB connection and cache it"""
    return MongoClient(uri)

@st.cache_data
def get_dataframe(selected_date, _collection):
    """Query MongoDB for documents on the selected date and return as a DataFrame"""
    docs = _collection.find({"date": {"$gte": selected_date, "$lt": selected_date + pd.DateOffset(days=1)}})
    df = pd.DataFrame(list(docs))
    return df

def main():
    # Connect to MongoDB and get the collection
    client = get_mongo_client('mongodb://root:example@mongodb:27017/')
    
    # Set Streamlit page configuration
    st.image(Image.open('logo.png'))
    st.title("Streamlit AgGrid Application with MongoDB")

    db = client.test
    collection = db.test_collection

    st.write("Connected to MongoDB server.")

    # Check if the selected_date exists in the session state
    if 'selected_date' not in st.session_state:
        # Get the first document sorted by date
        first_doc = collection.find_one(sort=[("date", 1)])  
        st.session_state.selected_date = first_doc['date'].date()

    # Date selection
    selected_date = st.date_input('Select date', value=st.session_state.selected_date)

    # Format the date as "d m y"
    formatted_date = selected_date.strftime('Day: %d / Month: %m / Year: %Y')

    # Display the formatted date
    st.write(formatted_date)

    # Store the selected date in the session state
    if st.session_state.selected_date != selected_date:
        st.session_state.selected_date = selected_date
        st.experimental_rerun()

    # Convert the date to pandas Timestamp for comparison
    selected_date = pd.Timestamp(selected_date)

    # Get data from MongoDB for the selected date
    df = get_dataframe(selected_date, collection)

    # Check if the DataFrame is empty
    if df.empty:
        st.markdown("<span style='color: red;'>There is no registry in this time.</span>", unsafe_allow_html=True)
    else:
        # Continue if data is not empty...
        handle_data(df, selected_date)

def handle_data(df, selected_date):
    """Handles data display and interaction"""
    st.write("Click on a row to display its image:")

    # Check if 'start_hour' and 'end_hour' exist in the session state
    if 'start_hour' not in st.session_state:
        st.session_state.start_hour = 0  # default value
    if 'end_hour' not in st.session_state:
        st.session_state.end_hour = 23  # default value

    # Use session state values for the select boxes
    start_hour = st.selectbox('Select start hour', range(0, 24), index=0)
    end_hour = st.selectbox('Select end hour', range(1, 25), index=23)  # subtract 1 to convert to 0-based index

    # Update session state values immediately after the selectboxes
    st.session_state.start_hour = start_hour
    st.session_state.end_hour = end_hour

    # Check if the end time is earlier than the start time
    if end_hour <= start_hour:
        st.markdown("<span style='color: red;'>End hour should be later than start hour.</span>", unsafe_allow_html=True)
    else:
        # Continue if end hour is later than start hour...
        handle_hours(df, selected_date, start_hour, end_hour)

def handle_hours(df, selected_date, start_hour, end_hour):
    """Handles hour selection and data filtering"""

    # Convert selected hours to pandas Timestamp for comparison
    start_time = pd.Timestamp(selected_date.year, selected_date.month, selected_date.day, start_hour)

    # Set end_time based on the selected end hour
    if end_hour == 24:
        end_time = pd.Timestamp(selected_date.year, selected_date.month, selected_date.day+1, 0)  # set to beginning of next day
    else:
        end_time = pd.Timestamp(selected_date.year, selected_date.month, selected_date.day, end_hour, 1)  # Include an extra minute

    # Filter the DataFrame
    df = df[(df['date'] >= start_time) & (df['date'] < end_time)]
    st.write(f"There are {len(df)} registries.")
    
    # Continue if DataFrame is not empty...
    if len(df) > 0:
        handle_filtered_data(df, selected_date, start_hour, end_hour)

def handle_filtered_data(df, selected_date, start_hour, end_hour):
    """Handles the display and interaction of the filtered data"""

    # Exclude 'Image' and '_id' columns from the df used for AgGrid
    df_aggrid = df.drop(columns=['Image', '_id'])
    
    # Duplicate last row if df_aggrid has more than 12 rows
    if len(df_aggrid) >=12:
        last_row = df_aggrid.iloc[-1]
        df_aggrid.loc[len(df)]  = last_row
        df_aggrid = df_aggrid.reset_index(drop=True)

    # Configure grid options for single row selection without checkboxes and enable sorting
    grid_options_builder = GridOptionsBuilder.from_dataframe(df_aggrid)
    grid_options_builder.configure_selection("single", use_checkbox=False, groupSelectsFiltered=True)
    grid_options_builder.configure_default_column(
        sortable=True,
        filter=True
    )
    gridOptions = grid_options_builder.build()

    # Display AgGrid with configured options
    response = AgGrid(
        df_aggrid,
        gridOptions=gridOptions,
        height=400,
        width="100%",
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        key=f'table-{selected_date}-{start_hour}-{end_hour}'
    )

    # Display the image of the selected row
    if 'selected_rows' in response and len(response['selected_rows']) > 0:
        selected_row_data = response['selected_rows'][0]
        selected_row_data = selected_row_data['_selectedRowNodeInfo']['nodeRowIndex']
        if selected_row_data < len(df):
            st.write(f"You clicked row {selected_row_data + 1}")
            st.write(df_aggrid.iloc[selected_row_data]['ID'])

            # Decode and display the image
            base64_image = df.iloc[selected_row_data]['Image']
            bytes_image = base64.b64decode(base64_image)
            img = Image.open(io.BytesIO(bytes_image))
            st.image(img)

# Entry point of the script
if __name__ == "__main__":
    main()
