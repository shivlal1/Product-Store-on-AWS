package main

import (
	"net/http"
	"sync"

	"github.com/gin-gonic/gin"
)

// Product represents data about a product
type Product struct {
	ID          string  `json:"id" binding:"required"`
	Name        string  `json:"name" binding:"required"`
	Description string  `json:"description"`
	Price       float64 `json:"price" binding:"required,gt=0"`
	Stock       int     `json:"stock" binding:"min=0"`
}

// ProductStore manages our in-memory product storage
type ProductStore struct {
	mu       sync.RWMutex
	products map[string]Product
}

// Global product store
var store = &ProductStore{
	products: make(map[string]Product),
}

// Initialize with some sample data
func init() {
	sampleProducts := []Product{
		{ID: "1", Name: "Laptop", Description: "High-performance laptop", Price: 999.99, Stock: 10},
		{ID: "2", Name: "Mouse", Description: "Wireless mouse", Price: 29.99, Stock: 50},
		{ID: "3", Name: "Keyboard", Description: "Mechanical keyboard", Price: 89.99, Stock: 25},
	}

	for _, p := range sampleProducts {
		store.products[p.ID] = p
	}
}

func main() {
	router := gin.Default()

	// Product routes
	router.GET("/products", getProducts)
	router.GET("/products/:id", getProductByID)
	router.POST("/products", createProduct)

	router.Run(":8080")
}

// getProducts returns all products
// Returns: 200 OK - Success (Happy cat with coffee!)
func getProducts(c *gin.Context) {
	store.mu.RLock()
	defer store.mu.RUnlock()

	// Convert map to slice for response
	products := make([]Product, 0, len(store.products))
	for _, product := range store.products {
		products = append(products, product)
	}

	c.JSON(http.StatusOK, gin.H{
		"count":    len(products),
		"products": products,
	})
}

// getProductByID returns a single product by ID
// Returns: 200 OK - Found (Happy cat!)
// Returns: 404 Not Found - Product doesn't exist (Cat hiding in a box!)
func getProductByID(c *gin.Context) {
	id := c.Param("id")

	store.mu.RLock()
	defer store.mu.RUnlock()

	product, exists := store.products[id]
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "Product not found",
			"id":    id,
		})
		return
	}

	c.JSON(http.StatusOK, product)
}

// createProduct adds a new product
// Returns: 201 Created - Success (Cat with a party hat!)
// Returns: 400 Bad Request - Invalid input (Confused cat!)
// Returns: 409 Conflict - Product ID already exists (Fighting cats!)
func createProduct(c *gin.Context) {
	var newProduct Product

	// Validate and bind JSON
	if err := c.ShouldBindJSON(&newProduct); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid product data",
			"details": err.Error(),
		})
		return
	}

	store.mu.Lock()
	defer store.mu.Unlock()

	// Check if product ID already exists
	if _, exists := store.products[newProduct.ID]; exists {
		c.JSON(http.StatusConflict, gin.H{
			"error": "Product with this ID already exists",
			"id":    newProduct.ID,
		})
		return
	}

	// Add the new product
	store.products[newProduct.ID] = newProduct

	c.JSON(http.StatusCreated, gin.H{
		"message": "Product created successfully",
		"product": newProduct,
	})
}

// Additional validation helper (optional)
func validateProduct(p Product) []string {
	var errors []string

	if p.Name == "" {
		errors = append(errors, "Product name is required")
	}

	if len(p.Name) > 100 {
		errors = append(errors, "Product name too long (max 100 characters)")
	}

	if p.Price <= 0 {
		errors = append(errors, "Price must be greater than 0")
	}

	if p.Stock < 0 {
		errors = append(errors, "Stock cannot be negative")
	}

	return errors
}
