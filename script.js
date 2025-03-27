let pointsTable = [];
let predictions = {
  "Kunal": {"SRH": 1, "MI": 2, "DC": 3, "CSK": 4, "KKR": 5, "GT": 6, "RCB": 7, "RR": 8, "LSG": 9, "PBKS": 10},
  "Ankit": {"MI": 1, "SRH": 2, "CSK": 3, "KKR": 4, "RCB": 5, "GT": 6, "DC": 7, "LSG": 8, "PBKS": 9, "RR": 10},
  "Pradeep": {"RCB": 1, "CSK": 2, "KKR": 3, "MI": 4, "SRH": 5, "DC": 6, "LSG": 7, "RR": 8, "PBKS": 9, "GT": 10},
  "Rathi": {"SRH": 1, "MI": 2, "CSK": 3, "KKR": 4, "DC": 5, "RCB": 6, "PBKS": 7, "GT": 8, "LSG": 9, "RR": 10},
  "Rajat": {"CSK": 1, "RR": 2, "SRH": 3, "DC": 4, "KKR": 5, "PBKS": 6, "MI": 7, "RCB": 8, "LSG": 9, "GT": 10},
  "Bairathi": {"MI": 1, "CSK": 2, "SRH": 3, "KKR": 4, "PBKS": 5, "RCB": 6, "DC": 7, "GT": 8, "LSG": 9, "RR": 10},
  "Sid": {"SRH": 1, "DC": 2, "CSK": 3, "PBKS": 4, "MI": 5, "KKR": 6, "RR": 7, "GT": 8, "RCB": 9, "LSG": 10},
  "Vineet": {"MI": 1, "SRH": 2, "KKR": 3, "RCB": 4, "CSK": 5, "GT": 6, "PBKS": 7, "DC": 8, "RR": 9, "LSG": 10}
};
let totals = {};
let players = Object.keys(predictions);

// Function to convert a JavaScript array to a table
function convertArrayToTable(array, tableId) {
  const table = document.getElementById(tableId);

  array.forEach(rowData => {
    const row = document.createElement('tr'); // Create a new row

    rowData.forEach(cellData => {
      const cell = document.createElement('td'); // Create a new cell
      cell.textContent = cellData; // Add data to the cell
      row.appendChild(cell); // Append the cell to the row
    });

    table.appendChild(row); // Append the row to the table
  });
}

async function fetchPointsTable() {
  const proxyUrl = '/.netlify/functions/proxy'; // Proxy endpoint hosted on Netlify

  try {
    console.log('Fetching points table from proxy...'); // Debug log

    const response = await fetch(proxyUrl); // Fetch data from the proxy
    if (!response.ok) throw new Error(`Failed to fetch points table: ${response.status}`);

    const data = await response.json(); // Parse the response JSON
    console.log('Data received from proxy:', data); // Log the raw response data

    // Validate the structure of the response
    if (!data || Object.keys(data).length === 0) {
      throw new Error('Invalid data structure: no team data found');
    }

    // Sort the keys numerically (e.g., "Team 1", "Team 2", ...)
    const sortedKeys = Object.keys(data).sort((a, b) => {
      // Extract the numeric part of the keys and sort them
      const numA = parseInt(a.replace('Team ', ''));
      const numB = parseInt(b.replace('Team ', ''));
      return numA - numB;
    });

    // Convert the sorted data into a 2D list (table format)
    const teamShortNames = {
      "Sunrisers Hyderabad": "SRH",
      "Rajasthan Royals": "RR",
      "Royal Challengers Bengaluru": "RCB",
      "Punjab Kings": "PBKS",
      "Chennai Super Kings": "CSK",
      "Delhi Capitals": "DC",
      "Kolkata Knight Riders": "KKR",
      "Lucknow Super Giants": "LSG",
      "Mumbai Indians": "MI",
      "Gujarat Titans": "GT"
    };

    const table = [
      ["Team", "M", "W", "L", "T", "N/R", "PT", "NRR"] // Table headers
    ];

    // Iterate over the sorted keys and process the data
    sortedKeys.forEach(key => {
      const team = data[key];
      const row = [
        teamShortNames[team.Name] || team.Name, // Fallback to full name if short name is not available
        team.Played,                            // Matches (M)
        team.Won,                               // Wins (W)
        team.Loss,                              // Losses (L)
        team.Draw || 0,                         // Draws (T, default to 0)
        team['No Result'] || 0,                 // No Result (N/R, default to 0)
        team.Points,                            // Points (PT)
        team['Net Run Rate']                    // Net Run Rate (NRR)
      ];
      console.log('Adding row to table:', row); // Debug log for each row
      table.push(row);
    });

    console.log('Final sorted table:', table); // Log the final table
    return table; // Return the formatted table
  } catch (error) {
    console.error('Error fetching points table:', error); // Log the error
    return []; // Return an empty table on error
  }
}

(async () => {
  let playerTotal
  pointsTable = await fetchPointsTable(); // Calls the function to populate the pointsTable variable
  console.log('Points Table:', pointsTable); // Logs the pointsTable variable
  // console.log(Math.abs(2 - predictions["Kunal"][pointsTable[2][0]]))
  players.forEach((player) => {
    playerTotal = 0;
    for (let j = 1; j <= 10; j++) {
      playerTotal += Math.abs(j - predictions[player][pointsTable[j][0]]);
    }
    totals[player] = playerTotal;
  })
  totals = Object.fromEntries(Object.entries(totals).sort((a, b) => a[1] - b[1]))
  console.log("New totals: ", totals);
  console.log("JSON data: ", JSON.stringify(totals))
  const tableWidth = pointsTable[0].length;
  players = Object.keys(totals);
  for (let x = 0; x < players.length; x++) {
    pointsTable[0][pointsTable[0].length] = players[x];
    for (let y = 1; y < pointsTable.length; y++) {
      let prediction = predictions[players[x]][pointsTable[y][0]];
      pointsTable[y][tableWidth + x] = `${Math.abs(y - prediction)} (${prediction})`;
    }
  }
  let z = pointsTable.length
  pointsTable[z] = ["", "", "", "", "", "", "","Totals"];
  pointsTable[z] = pointsTable[z].concat(Object.values(totals));
  console.log("New log for pointsTable: ", pointsTable);
  console.log("New JSON log for pointsTable: ", JSON.stringify(pointsTable));
  convertArrayToTable(pointsTable, 'myTable');
})();