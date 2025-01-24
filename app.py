if response.status_code == 200:
    llm_response = response.json()['choices'][0]['message']['content']
    st.subheader("LLM Response")
    st.write(llm_response)  # Display the raw response for debugging

    # Parse LLM response for chart details
    try:
        # Clean the response to ensure valid JSON
        llm_response = llm_response.strip()  # Remove extra whitespace
        if llm_response.startswith("```") and llm_response.endswith("```"):
            llm_response = llm_response[3:-3]  # Remove markdown code block delimiters

        # Attempt to parse the JSON
        chart_details = json.loads(llm_response)
        chart_type = chart_details.get("chart_type")
        x_col = chart_details.get("x_col")
        y_col = chart_details.get("y_col")
        group_by = chart_details.get("group_by")

        # Generate the requested chart
        generate_chart(chart_type, x_col, y_col, group_by)

    except json.JSONDecodeError:
        st.error("Failed to parse LLM response. The response might not be in the expected JSON format.")
        st.write("Raw Response:")
        st.code(llm_response, language="json")  # Show the raw response for user debugging
    except Exception as e:
        st.error(f"Error generating chart: {e}")
else:
    st.error(f"Error from Azure OpenAI API: {response.status_code} - {response.text}")
