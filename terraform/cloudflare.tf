# Cloudflare Provider Configuration
provider "cloudflare" {
  email = "your-email@example.com"  # Your Cloudflare account email
  api_key = "your_api_key"          # Your Cloudflare API key
}

# Create a Cloudflare Worker
resource "cloudflare_worker_script" "llama_worker" {
  name = "llama-worker"

  content = <<EOF
  addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request))
  })

  async function handleRequest(request) {
    const url = "https://api.cloudflare.com/client/v4/accounts/1c49a64fcdcf951fc1c9cfef24f93ff3/ai/run/@cf/meta/llama-3.2-11b-vision-instruct";

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer YOUR_CLOUDFLARE_API_TOKEN'  // Replace with your Cloudflare API token
      }
    });

    return new Response(await response.text(), {
      status: response.status,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
  EOF
}

# Publish the Worker
resource "cloudflare_worker_route" "llama_route" {
  zone_id = "your_zone_id"  # Replace with your Cloudflare Zone ID
  pattern = "your-domain.com/llama"  # Change to your desired route pattern
  script_name = cloudflare_worker_script.llama_worker.name
}