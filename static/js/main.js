document.getElementById("submit-btn").addEventListener("click", function () {
    let query = document.getElementById("user-query").value.trim();
    if (query === "") {
        alert("Please enter a query.");
        return;
    }

    // Display the user's query in chat
    displayMessage(query, "user");

    // Send query to Flask backend
    fetch("/get_response", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayMessage(data.response, "bot");
        } else {
            displayMessage("Sorry, I couldn't process that query.", "bot");
        }
    })
    .catch(error => {
        console.error("Error:", error);
        displayMessage("Something went wrong. Try again!", "bot");
    });

    // Clear input field after sending
    document.getElementById("user-query").value = "";
});

// Function to display messages in the chatbox
function displayMessage(msg, sender) {
    let chatBox = document.getElementById("chat-history");
    let msgDiv = document.createElement("div");
    msgDiv.className = sender === "user" ? "user-msg" : "bot-msg";
    msgDiv.textContent = msg;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Logout functionality (redirect to login page or perform other actions)
function logout() {
    window.location.href = "/logout"; // Redirect to logout URL
}
