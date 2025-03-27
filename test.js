let dictionary = {
  "Team 1": 3,
  "Team 2": 1,
  "Team 3": 5,
  "Team 4": 2
};

dictionary = Object.fromEntries(Object.entries(dictionary).sort((a, b) => a[1] - b[1]));
console.log(dictionary);