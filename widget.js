function ready(fn) {
  if (document.readyState !== 'loading'){
    fn();
  } else {
    document.addEventListener('DOMContentLoaded', fn);
  }
}

// Specify the names of your columns
const urlColumn = 'URL';         // Column containing the URL
const contentColumn = 'Content'; // Column to store the HTML content

let app = undefined;
let data = {
  status: 'waiting',
  url: null,
};

function handleError(err) {
  console.error('ERROR', err);
  data.status = String(err).replace(/^Error: /, '');
}

async function fetchAndUpdateContent(url, recordId, tableId) {
  data.status = "Fetching content...";
  try {
    // Fetch the HTML content from the URL
    let response = await fetch(url);

    if (response.ok) {
      let htmlContent = await response.text();

      data.status = 'Content fetched. Updating Grist...';

      // Get the Grist document API
      let docApi = await grist.docApi;

      // Update the 'Content' column in Grist
      await docApi.updateRecords(tableId, {
        id: [recordId],
        fields: {
          [contentColumn]: [htmlContent],
        }
      });

      data.status = 'Content updated successfully.';
    } else {
      data.status = 'Error fetching content: ' + response.statusText;
    }
  } catch (error) {
    data.status = 'Fetch error: ' + error.message;
  }
}

function onRecord(record, mappings) {
  try {
    data.status = '';
    // Map the column names
    record = grist.mapColumnNames(record) || record;

    let url = record[urlColumn];
    let recordId = record.id;
    let tableId = mappings.tableId;

    if (!url) {
      data.status = 'No URL provided.';
      data.url = null;
      return;
    }

    data.url = url;

    // Optional: Automatically fetch content when the URL changes
    // Uncomment the next line if you want automatic fetching
    // fetchAndUpdateContent(url, recordId, tableId);

  } catch (err) {
    handleError(err);
  }
}

async function onFetchButtonClick() {
  if (data.url) {
    let record = await grist.selectedRecord;
    let mappings = await grist.mappings;
    let recordId = record.id;
    let tableId = mappings.tableId;
    await fetchAndUpdateContent(data.url, recordId, tableId);
  } else {
    data.status = 'No URL to fetch.';
  }
}

ready(function() {
  grist.ready({columns: [{name: urlColumn}, {name: contentColumn}]});
  grist.onRecord(onRecord);
  const mapped = grist.mapColumnNames(record);
  Vue.config.errorHandler = handleError;
  app = new Vue({
    el: '#app',
    data: data,
    methods: {onFetchButtonClick}
  });
});
