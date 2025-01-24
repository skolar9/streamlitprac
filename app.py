with col2:
    st.header("Ask Inventory Questions")
    user_query = st.text_input("Enter your query:")
    
    if st.button("Submit"):
        # Use LangChain to process query
        prompt = PromptTemplate(
            input_variables=["query", "columns"],
            template=(
                "You are an inventory analyst. Given the dataset with columns {columns}, "
                "analyze the inventory and answer the following: {query}. Suggest charts if needed."
            )
        )
        structured_query = prompt.format(query=user_query, columns=", ".join(inventory_data.columns))
        response = llm.predict_messages([{"role": "user", "content": structured_query}])

        st.subheader("LLM Response")
        st.write(response.content)

        # Parse LLM response for chart details
        try:
            chart_details = eval(response.content)  # Ensure the response contains chart instructions
            chart_type = chart_details.get("chart_type")
            x_col = chart_details.get("x_col")
            y_col = chart_details.get("y_col")
            group_by = chart_details.get("group_by")

            # Generate the requested chart
            def generate_chart(chart_type, x_col, y_col=None, group_by=None):
                fig, ax = plt.subplots(figsize=(10, 6))
                if chart_type == "bar":
                    grouped_data = inventory_data.groupby(group_by)[y_col].sum().reset_index()
                    ax.bar(grouped_data[group_by], grouped_data[y_col], color="skyblue")
                    ax.set_title(f"{y_col} by {group_by}")
                    ax.set_xlabel(group_by)
                    ax.set_ylabel(y_col)
                elif chart_type == "pie":
                    grouped_data = inventory_data.groupby(group_by)[y_col].sum().reset_index()
                    ax.pie(grouped_data[y_col], labels=grouped_data[group_by], autopct='%1.1f%%', startangle=90)
                    ax.set_title(f"Distribution of {y_col} by {group_by}")
                elif chart_type == "line":
                    grouped_data = inventory_data.groupby(x_col)[y_col].sum().reset_index()
                    ax.plot(grouped_data[x_col], grouped_data[y_col], marker='o')
                    ax.set_title(f"{y_col} over {x_col}")
                    ax.set_xlabel(x_col)
                    ax.set_ylabel(y_col)
                elif chart_type == "scatter":
                    ax.scatter(inventory_data[x_col], inventory_data[y_col], color='blue')
                    ax.set_title(f"Scatter Plot of {y_col} vs {x_col}")
                    ax.set_xlabel(x_col)
                    ax.set_ylabel(y_col)
                elif chart_type == "histogram":
                    ax.hist(inventory_data[y_col], bins=20, color='lightgreen')
                    ax.set_title(f"Histogram of {y_col}")
                    ax.set_xlabel(y_col)
                    ax.set_ylabel('Frequency')
                elif chart_type == "box":
                    ax.boxplot(inventory_data[y_col])
                    ax.set_title(f"Box Plot of {y_col}")
                elif chart_type == "heatmap":
                    correlation = inventory_data.corr()
                    sns.heatmap(correlation, annot=True, cmap="coolwarm", ax=ax)
                    ax.set_title("Correlation Heatmap")
                elif chart_type == "stacked_bar":
                    stacked_data = inventory_data.groupby([group_by, x_col])[y_col].sum().unstack().fillna(0)
                    stacked_data.plot(kind='bar', stacked=True, ax=ax)
                    ax.set_title(f"Stacked Bar Chart of {y_col} by {group_by} and {x_col}")
                else:
                    st.write("Chart type not supported yet.")
                st.pyplot(fig)

            generate_chart(chart_type, x_col, y_col, group_by)

        except Exception as e:
            st.error(f"Error generating chart: {e}")
