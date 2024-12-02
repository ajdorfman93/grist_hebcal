// Initialize Vue.js data object
let appData = {
  status: '',
  url: null,
  content: null
};

// Function to handle errors
function handleError(err) {
  console.error('ERROR', err);
  appData.status = String(err).replace(/^Error: /, '');
}

// Function to fetch and update content
async function fetchAndUpdateContent(url, recordId, tableId) {
  appData.status = "Fetching content...";
  try {
    // Fetch the HTML content from the URL
    let response = await fetch(url);
    if (response.ok) {
      let htmlContent = await response.text();

      appData.status = 'Content fetched. Updating Grist...';

      // Sanitize the HTML content
      let sanitizedContent = DOMPurify.sanitize(htmlContent);

      // Get the Grist document API
      let docApi = await grist.docApi;

      // Update the 'Content' column in Grist
      await docApi.updateRecords(tableId, {
        id: [recordId],
        fields: {
          'Content': [sanitizedContent],
        }
      });

      appData.status = 'Content updated successfully.';
      appData.content = sanitizedContent; // Display the content in the widget

    } else {
      appData.status = 'Error fetching content: ' + response.statusText;
    }
  } catch (error) {
    appData.status = 'Fetch error: ' + error.message;
  }
}

// Function to handle record changes
function onRecord(record, mappings) {
  try {
    appData.status = '';
    appData.content = null;

    // Map the column names
    let mappedRecord = grist.mapColumnNames(record);
    let url = mappedRecord ? mappedRecord.URL : record.URL;
    let recordId = record.id;
    let tableId = mappings.tableId;

    if (!url) {
      appData.status = 'No URL provided.';
      appData.url = null;
      return;
    }

    appData.url = url;

  } catch (err) {
    handleError(err);
  }
}

// Function to handle fetch button click
async function onFetchButtonClick() {
  if (appData.url) {
    try {
      let record = await grist.selectedRecord;
      let mappings = await grist.mappings;
      let recordId = record.id;
      let tableId = mappings.tableId;
      await fetchAndUpdateContent(appData.url, recordId, tableId);
    } catch (err) {
      handleError(err);
    }
  } else {
    appData.status = 'No URL to fetch.';
  }
}

// Initialize the widget
grist.ready({
  columns: ['URL', 'Content'],
  requiredAccess: 'full'
});
grist.onRecord(onRecord);

// Create Vue.js app
new Vue({
  el: '#app',
  data: appData,
  methods: { onFetchButtonClick }
});
