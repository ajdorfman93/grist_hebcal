<!DOCTYPE html>
<html lang="en"> <!-- Specifies the language of the document as English -->
  <head>
    <meta charset="utf-8"> <!-- Sets the character encoding to UTF-8 -->
    <title>Render sanitized HTML from a cell or display content from a URL</title> <!-- Sets the document title -->
    <script src="https://docs.getgrist.com/grist-plugin-api.js"></script> <!-- Loads the Grist Plugin API -->
    <script src="https://cdn.jsdelivr.net/npm/dompurify@2.2.9/dist/purify.min.js"></script> <!-- Loads DOMPurify for sanitizing HTML -->
    <style>
      html, body, textarea { /* Sets the style for the HTML, body, and textarea elements */
          display: inherit;
          padding: 0;
          margin: 0;
      }
      #error { /* Styles for the error display element */
          display: none;
          background: red;
          color: white;
          padding: 20px;
          text-align: center;
      }
      iframe { /* Removes borders from iframe elements */
          border: none;
      }
    </style>
  </head>
  <body>
    <div id="error"></div> <!-- Div for displaying error messages -->
    <div id="rendered"></div> <!-- Div for rendering sanitized HTML or iframe content -->
    <script>
      // Include the ready function
      function ready(fn) {
        if (document.readyState !== 'loading'){ // If the document is already loaded
          fn(); // Execute the callback function
        } else {
          document.addEventListener('DOMContentLoaded', fn); // Otherwise, wait until DOMContentLoaded
        }
      }

      var params = new URLSearchParams(window.location.search); // Parse URL parameters
      var ADD_TAGS = params.get('tags')?.split(","); // Optional list of additional allowed tags
      var ADD_ATTR = params.get('attr')?.split(","); // Optional list of additional allowed attributes

      // Function to check if a string is a valid URL
      function isValidUrl(string) {
        try {
          new URL(string); // Attempt to create a URL object
          return true; // If successful, the string is a valid URL
        } catch (_) {
          return false; // Otherwise, it's not a valid URL
        }
      }

      // Handle errors
      function handleError(err) {
        console.error('ERROR', err); // Log the error to the console
        document.getElementById('error').innerText = String(err).replace(/^Error: /, ''); // Display the error message
        document.getElementById('error').style.display = 'block'; // Make the error div visible
      }

      // Function to apply actions to Grist
      async function applyActions(actions) {
        try {
          await grist.docApi.applyUserActions(actions); // Apply actions via the Grist API
          console.log('Added new row successfully.'); // Log success message
        } catch (e) {
          console.error('Error applying actions:', e); // Log errors
          handleError(e); // Display the error
        }
      }

      // Function to add a new row to a different table
      function addRowToTable(htmlContent) {
        const tableId = 'Times'; // ID of the target table
        const columnValues = {
          'HtmlContent': htmlContent // Set the HtmlContent column with the provided content
        };
        const actions = [
          ['AddRecord', tableId, null, columnValues] // Add a record with the specified column values
        ];
        applyActions(actions); // Apply the action
      }

      function render(elemId, content) {
        var el = document.getElementById(elemId); // Get the element by ID
        if (!content) { // If no content is provided
          el.style.display = 'none'; // Hide the element
        } else {
          el.innerHTML = ''; // Clear the existing content
          if (isValidUrl(content)) { // Check if the content is a valid URL
            var iframe = document.createElement('iframe'); // Create an iframe
            iframe.src = content; // Set the iframe source to the URL
            iframe.style.width = 'inherit'; // Set the iframe width
            iframe.style.height = 'inherit'; // Set the iframe height
            el.appendChild(iframe); // Append the iframe to the element

            // Fetch HTML content from the URL and add it to the table
            fetch(content)
              .then(response => response.text())
              .then(htmlContent => {
                addRowToTable(htmlContent); // Add the fetched content to the Grist table
              })
              .catch(error => {
                console.error('Error fetching URL content:', error); // Log fetch errors
                handleError(error); // Display the error
              });

          } else { // If the content is not a URL
            const sanitizedContent = DOMPurify.sanitize(content, {ADD_TAGS, ADD_ATTR}); // Sanitize the HTML content
            el.innerHTML = sanitizedContent; // Set the sanitized content to the element

            // If we are allowing scripts, let them execute
            if (ADD_TAGS?.includes("script")) {
              Array.from(el.querySelectorAll("script")).forEach(oldScript => { // Replace each script tag
                const newScript = document.createElement("script");
                Array.from(oldScript.attributes) // Copy attributes
                  .forEach(attr => newScript.setAttribute(attr.name, attr.value));
                newScript.appendChild(document.createTextNode(oldScript.innerHTML)); // Copy the script content
                oldScript.parentNode.replaceChild(newScript, oldScript); // Replace the old script with the new one
              });
            }

            // Add the HTML content to the table
            addRowToTable(content);
          }
          el.style.display = 'block'; // Make the element visible
        }
      }

      let lastId = undefined; // Variable to track the last processed record ID
      let lastData = undefined; // Variable to track the last processed record data

      // Helper function that reads the first value from a table with a single column
      function singleColumn(record) {
        const columns = Object.keys(record || {}).filter(k => k !== 'id'); // Get non-ID columns
        return columns.length === 1 ? record[columns[0]] : undefined; // Return the first column value, if only one exists
      }

      // Ready function to ensure the DOM is loaded
      ready(function() {
        grist.ready({
          columns: ["Html"], // Request access to the "Html" column
          requiredAccess: 'full' // Request full access to allow row additions
        });

        grist.onNewRecord(() => { // Handle new records
          render("error", null); // Clear the error element
          render("rendered", ""); // Clear the rendered element
          lastData = ""; // Reset the last data
          lastId = 0; // Reset the last ID
        });

        grist.onRecord(function(record) { // Handle updates to existing records
          try {
            const mapped = grist.mapColumnNames(record); // Map column names if a mapping is provided
            const data = mapped ? mapped.Html : singleColumn(record); // Use mapped column or fallback to a single column
            if (data === undefined) {
              render("error", "Please choose a column to show in the Creator Panel."); // Display an error if no data is available
            } else {
              render("error", null); // Clear errors
              if (lastId !== record.id || lastData !== data) { // Check for changes
                render("rendered", String(data || '')); // Render the updated data
              }
              lastId = record.id; // Update the last processed ID
              lastData = data; // Update the last processed data
            }
          } catch (err) {
            handleError(err); // Handle and display errors
          }
        });
      });
    </script>
  </body>
</html>
