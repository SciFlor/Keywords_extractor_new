import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime
import os
import io
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)


def extract_keywords(text):
    try:
        response = requests.post('http://keyword_extractor:5000/extract', json={'text': text}, timeout=300)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error processing keywords: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None


def create_output_folder(source_name):
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{source_name}_{current_time}_keyword_extraction"
    os.makedirs(folder_name, exist_ok=True)
    return folder_name


def save_dataframe(df, folder_path, file_name):
    # Save as CSV
    csv_path = os.path.join(folder_path, f"{file_name}.csv")
    df.to_csv(csv_path, index=False)

    # Save as JSON
    json_path = os.path.join(folder_path, f"{file_name}.json")
    df.to_json(json_path, orient="records", indent=2)

    # Save as Excel
    excel_path = os.path.join(folder_path, f"{file_name}.xlsx")
    df.to_excel(excel_path, index=False, engine="openpyxl")


def main():
    st.set_page_config(layout="wide")

    st.title("Keyword Extractor")

    st.sidebar.title("About")
    st.sidebar.write("""
    This app extracts keywords from chapters in the JSON output of the Chapter Extractor app.

    **How it works:**
    1. Upload the JSON file containing chapter data.
    2. The app processes all chapters automatically.
    3. Keywords are extracted for each chapter.
    4. View and download the results.

    **Trust Intervals:**
    - 0.8 - 1.0: High relevance
    - 0.5 - 0.79: Medium relevance
    - 0.0 - 0.49: Low relevance
    """)

    uploaded_file = st.file_uploader("Choose a JSON file", type=['json'])

    if uploaded_file is not None:
        try:
            json_data = json.load(uploaded_file)
            st.success("JSON file loaded successfully!")

            if isinstance(json_data, list) and len(json_data) > 0:
                df = pd.DataFrame(json_data)

                st.subheader("Processing Chapters")
                progress_bar = st.progress(0)
                status_text = st.empty()

                results = []
                for idx, row in df.iterrows():
                    progress = (idx + 1) / len(df)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing chapter {idx + 1} of {len(df)}")
                    text = row['Chapter Text']
                    keywords = extract_keywords(text)
                    if keywords:
                        results.append({
                            'Chapter': row['Chapter Name'],
                            'Keywords': ', '.join(keywords.keys()),
                            'Details': keywords
                        })

                progress_bar.empty()
                status_text.empty()

                if results:
                    results_df = pd.DataFrame(results)

                    st.subheader("Extracted Keywords Overview")
                    st.dataframe(results_df[['Chapter', 'Keywords']])

                    st.subheader("Detailed Keyword Information")
                    chapter_select = st.selectbox("Select a chapter to view detailed information",
                                                  results_df['Chapter'])

                    if chapter_select:
                        chapter_data = results_df[results_df['Chapter'] == chapter_select].iloc[0]
                        st.write(f"Chapter: {chapter_data['Chapter']}")
                        st.write("Keywords:")

                        details_df = pd.DataFrame.from_dict(chapter_data['Details'], orient='index')
                        details_df.reset_index(inplace=True)
                        details_df.columns = ['Keyword', 'Frequency', 'Trust Interval']
                        details_df = details_df.sort_values('Trust Interval', ascending=False)

                        st.dataframe(details_df)

                    # Prepare data for download
                    download_data = []
                    for _, row in results_df.iterrows():
                        for keyword, details in row['Details'].items():
                            download_data.append({
                                'Chapter': row['Chapter'],
                                'Keyword': keyword,
                                'Frequency': details['frequency'],
                                'Trust Interval': details['trust_interval']
                            })

                    download_df = pd.DataFrame(download_data)

                    if st.button("Save All Tables"):
                        source_name = uploaded_file.name.split('.')[0]
                        folder_path = create_output_folder(source_name)

                        # Save overview table
                        save_dataframe(results_df[['Chapter', 'Keywords']], folder_path, "keywords_overview")

                        # Save detailed table
                        save_dataframe(download_df, folder_path, "keywords_detailed")

                        # Save individual chapter tables
                        for chapter in results_df['Chapter']:
                            chapter_data = download_df[download_df['Chapter'] == chapter]
                            save_dataframe(chapter_data, folder_path, f"chapter_{chapter.replace(' ', '_')}")

                        st.success(f"All tables have been saved in the folder: {folder_path}")

                    st.subheader("Download Results")

                    csv = download_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="keyword_extraction_results.csv",
                        mime="text/csv"
                    )

                    json_str = download_df.to_json(orient="records", indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name="keyword_extraction_results.json",
                        mime="application/json"
                    )

                    excel_buffer = io.BytesIO()
                    download_df.to_excel(excel_buffer, index=False, engine="openpyxl")
                    excel_data = excel_buffer.getvalue()
                    st.download_button(
                        label="Download Excel",
                        data=excel_data,
                        file_name="keyword_extraction_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No keywords were extracted. Please check the input data and try again.")
            else:
                st.error("Invalid JSON structure. Expected a list of objects.")

        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please upload a valid JSON file.")
        except Exception as e:
            logging.exception("An unexpected error occurred")
            st.error(f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    main()

