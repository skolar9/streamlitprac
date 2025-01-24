prompt = PromptTemplate(
    input_variables=["query", "columns"],
    template=(
        "You are an inventory analyst. Given the dataset with columns {columns}, "
        "analyze the inventory and answer the following: {query}. "
        "Here is a description of the columns:\n"
        "- 'sku': The unique identifier for each product.\n"
        "- 'total_pallets': The total number of pallets for the product.\n"
        "- 'status': The current status of the product.\n"
        "- 'crested_date': The date when the inventory was created.\n"
        "Return the response in the following format:\n"
        "{\n"
        "  'chart_type': 'type_of_chart',\n"
        "  'x_col': 'name_of_column_for_x',\n"
        "  'y_col': 'name_of_column_for_y',\n"
        "  'group_by': 'name_of_column_for_grouping' (optional),\n"
        "  'additional_notes': 'optional_notes_for_the_user'\n"
        "}\n"
        "The chart_type can be one of the following: 'bar', 'pie', 'line', 'scatter', 'histogram', 'box', 'heatmap', or 'stacked_bar'."
    )
)
