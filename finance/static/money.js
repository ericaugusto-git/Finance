//got from: https://stackoverflow.com/questions/149055/how-to-format-numbers-as-currency-strings
var formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
});

let field = document.querySelector("input[id = cash]")
field.addEventListener("input", () => {
    money.style.display = "block"
    if (field.value == 0){
        money.style.display = "none"
    }
    money.innerHTML = "Deposit: " + formatter.format(field.value)
});