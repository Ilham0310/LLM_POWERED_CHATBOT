

document.getElementById("chat-form").addEventListener("submit", async function(event) {
    event.preventDefault();

    const userInput = document.getElementById("user-input").value;
    if (!userInput.trim()) {
        displayMessage("Error: Please enter a message.", "bot-message");
        return;
    }
    document.getElementById("user-input").value = ""; // Clear input field

    // Display user's message in the chat
    displayMessage("You: " + userInput, "user-message");

    // Send request to Flask backend
    try {
        const response = await fetch("http://127.0.0.1:5000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userInput })
        });

        if (response.ok) {
            const data = await response.json();

            // Display the SQL query
            displayMessage("Generated SQL Query: " + data.sql_query, "sql-query");

            // Display results in a table format
            if (Array.isArray(data.response) && data.response.length > 0) {
                displayTable(data.response);
            } else {
                displayMessage("No results found.", "bot-message");
            }
        } else {
            displayMessage("Error: Could not fetch response from the server.", "bot-message");
        }
    } catch (error) {
        console.error("Error:", error);
        displayMessage("Error: Something went wrong.", "bot-message");
    }
});

function displayMessage(text, className) {
    const chatBox = document.getElementById("chat-box");
    const messageElement = document.createElement("p");
    messageElement.className = className;
    messageElement.textContent = text;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function displayTable(data) {
    const chatBox = document.getElementById("chat-box");

    // Remove any previous table
    const existingTable = document.querySelector(".result-table");
    if (existingTable) existingTable.remove();

    // Create a table element
    const table = document.createElement("table");
    table.className = "result-table";

    // Create the header row
    const headerRow = document.createElement("tr");
    Object.keys(data[0]).forEach(key => {
        const headerCell = document.createElement("th");
        headerCell.textContent = key;
        headerRow.appendChild(headerCell);
    });
    table.appendChild(headerRow);

    // Create the data rows
    data.forEach(row => {
        const dataRow = document.createElement("tr");
        Object.values(row).forEach(value => {
            const dataCell = document.createElement("td");
            dataCell.textContent = value || "N/A"; // Handle null/undefined values
            dataRow.appendChild(dataCell);
        });
        table.appendChild(dataRow);
    });

    // Append the table to the chat box
    chatBox.appendChild(table);
    chatBox.scrollTop = chatBox.scrollHeight;
}

