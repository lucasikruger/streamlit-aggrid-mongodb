import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from PIL import Image
import io
import base64

# Load data
df = pd.read_csv('output.csv')

# Convert your date column to datetime
df['date'] = pd.to_datetime(df['date'])

# Check if the selected_date exists in the session state
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = df['date'].min().date()

# Date selection
selected_date = st.date_input('Select date', min_value=df['date'].min().date(), max_value=df['date'].max().date(), value=st.session_state.selected_date)

# Store the selected date in the session state

if st.session_state.selected_date != selected_date:
    st.session_state.selected_date = selected_date
    st.experimental_rerun()
# Convert the date to pandas Timestamp for comparison
selected_date = pd.Timestamp(selected_date)

# Filter your DataFrame based on the selected date
df = df[df['date'].dt.date == selected_date.date()]

# Display the table using AgGrid
st.write("Click on a row to display its image:")

# Configure grid options for single row selection without checkboxes and enable sorting
grid_options_builder = GridOptionsBuilder.from_dataframe(df)
grid_options_builder.configure_selection("single", use_checkbox=False, groupSelectsFiltered=True)
grid_options_builder.configure_default_column(
    sortable=True,
    filter=True
)
gridOptions = grid_options_builder.build()

# Display AgGrid with configured options
response = AgGrid(
    df,
    gridOptions=gridOptions,
    height=400,
    width="100%",
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    fit_columns_on_grid_load=True,
    key=f'table-{selected_date}'
)

# Display the image of the selected row
if 'selected_rows' in response and len(response['selected_rows']) > 0:
    selected_row_data = response['selected_rows'][0]
    selected_row_data = selected_row_data['_selectedRowNodeInfo']['nodeRowIndex']
    st.write(f"You clicked row {selected_row_data + 1}")
    st.write(df.iloc[selected_row_data]['ID'])
    # Decode and display the image
    base64_image = df.iloc[selected_row_data]['Image']
    bytes_image = base64.b64decode(base64_image)
    img = Image.open(io.BytesIO(bytes_image))
    st.image(img)
