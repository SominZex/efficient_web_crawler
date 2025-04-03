let productLinks = [];

let productCards = document.querySelectorAll(".product-card-container a");

productCards.forEach(card => {
    let link = card.href;
    if (link) {
        productLinks.push(link);
    }
});

let csvContent = "data:text/csv;charset=utf-8,Link\n" + productLinks.join("\n");

let encodedUri = encodeURI(csvContent);

let link = document.createElement("a");
link.setAttribute("href", encodedUri);
link.setAttribute("download", "product_links.csv");
document.body.appendChild(link);

link.click();

document.body.removeChild(link);