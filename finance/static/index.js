//got from: https://stackoverflow.com/questions/149055/how-to-format-numbers-as-currency-strings
var formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
});
//HTML/CSS/JAVASCRIPT to dynamnic sizing textfield referecend from: https://css-tricks.com/auto-growing-inputs-textareas/
//Ps: I made alot of modifications to implement other functions besides the resizing
let el = document.querySelectorAll(".input-wrap .input");
let widthMachine = document.querySelectorAll(".input-wrap .width-machine");
let input = document.querySelectorAll("input[id = shares]")
//unformatted stock_total
let total = document.querySelectorAll("p[id = total]")
//unformatted price
let price = document.querySelectorAll("p[id = price]")
let the_total = document.querySelectorAll("td[id = total]")
let user_cash = document.querySelector("td[id = user_cash]")
//unformatted grand_total
let grand_total = document.querySelector("p[id = f_total]")
let form = document.querySelectorAll("form")
let entries = document.querySelectorAll("input[id = my-shares]")
var data = ""
let btn = document.getElementById("saveBtn")
btn.addEventListener("click", () =>{
    entries.item(0).value = data
    console.log(entries.item(0).value)
    btn.innerHTML = butt.innerHTML
    document.forms["form"].submit()
});
// Dealing with Input width
el.forEach( function(element,i){
    element.addEventListener("input", () => {
        widthMachine.item(i).innerHTML = element.value;
    });
});
//Change dynamically the html of the users_cash and stock_total based on the shares value
input.forEach(function(element, i) {
    element.addEventListener("input", () => {
        btn.style.display = "block";
        //calculate new stock_total
        let new_total = parseFloat(price.item(i).innerHTML) * element.value
        var list = []
        //save new_total in a hidden tag
        total.item(i).innerHTML = new_total
        //change stock_total HTML to that new_total
        the_total.item(i).innerHTML = formatter.format(new_total)
        let sum = 0
        //sum all the stocks_total on the hidden tag
        total.forEach(function(element){
            sum += parseFloat(element.innerHTML)
        });
        //change user_cash html based on the sum and the grand_total
        user_cash.innerHTML = formatter.format((parseFloat(grand_total.innerHTML) - sum))
        //create a list of dictionaries with the shares and it's stock_symbol
        form.forEach(function(element){
            const formData = new FormData(element)
            var dic = {}
            for (var pair of formData.entries()) {
                dic[pair[0]] = pair[1]
            }
            list.push(dic)
        });
        //save list as a JSON to be submited
        data = JSON.stringify(list);
    });
});
// Dealing with Textarea Height
function calcHeight(value) {
let numberOfLineBreaks = (value.match(/\n/g) || []).length;
// min-height + lines x line-height + padding + border
let newHeight = 20 + numberOfLineBreaks * 20 + 12 + 2;
return newHeight;
}