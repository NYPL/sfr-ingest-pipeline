module.exports = {
    "extends": [
        "airbnb"
    ],
    "rules": {
        "semi": 0,
        "no-useless-escape": 1,
        "prefer-destructuring": 1,
        "no-useless-catch": 1,
        "max-len": ["error", { "code": 140 }],
    },
    "env": {
        "browser": false
    }
};