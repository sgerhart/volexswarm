storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address = "0.0.0.0:8200"
  tls_disable = true
}

api_addr = "http://0.0.0.0:8200"
cluster_addr = "https://0.0.0.0:8201"
ui = true
disable_mlock = true

# For development/testing - remove in production
log_level = "INFO" 