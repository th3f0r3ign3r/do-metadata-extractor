# Function: Python Metadata Extractor

## Introduction

This repository contains a URL metadata extraction function written in Python. You can deploy it on DigitalOcean's App Platform as a Serverless Function component or as a standalone Function. Documentation is available at https://docs.digitalocean.com/products/functions.

### Requirements

- You need a DigitalOcean account. If you don't already have one, you can sign up at:

  [![DigitalOcean Referral Badge](https://web-platforms.sfo2.cdn.digitaloceanspaces.com/WWW/Badge%202.svg)](https://www.digitalocean.com/?refcode=4f3c5e4bc21d&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge)

- To deploy from the command line, you will need the [DigitalOcean `doctl` CLI](https://github.com/digitalocean/doctl/releases).

## Deploying the Function

```
# clone this repo
git clone git@github.com:th3f0r3ign3r/do-metadata-extractor.git
```

```
# deploy the project, using a remote build so that compiled executable matched runtime environment
doctl serverless deploy do-metadata-extractor --remote-build
```

The output from the deploy command will resemble the following.

```
Deploying 'do-metadata-extractor'
  to namespace 'fn-...'
  on host '...'
Deployment status recorded in 'do-metadata-extractor/.deployed'

Deployed functions ('doctl sls fn get <funcName> --url' for URL):
  - metadata/extract
```

## Using the Function

```
doctl serverless functions invoke metadata/extract
```

This will return the default response from the function.

```
{
  "statusCode": 400,
  "body": {
    "error": "Missing 'url' parameter"
  }
}
```

You can pass a parameter to your function using the `-p` command line argument.

```
doctl serverless functions invoke metadata/extract -p url:https://docs.docker.com/engine/network/packet-filtering-firewalls/#add-iptables-policies-before-dockers-rules
{
  "statusCode": 200,
  "body": {
    "url": "https://docs.docker.com/engine/network/packet-filtering-firewalls/#add-iptables-policies-before-dockers-rules",
    "title": "Packet filtering and firewalls",
    "description": "How Docker works with packet filtering, iptables, and firewalls",
    "image": "https://docs.docker.com/images/thumbnail.webp",
    "site_name": "Docker",
    "author": null,
    "domain": "docs.docker.com",
    "lang": "en",
    "canonical_url": "https://docs.docker.com/engine/network/packet-filtering-firewalls/",
    "favicon": "https://docs.docker.com/favicons/docs@2x.ico",
    "open_graph": {
      "description": "How Docker works with packet filtering, iptables, and firewalls",
      "title": "Packet filtering and firewalls",
      "type": "website",
      "updated_time": "2025-06-03 09:35:15 +0100 +0100",
      "image": "https://docs.docker.com/images/thumbnail.webp",
      "locale": "en_US",
      "url": "https://docs.docker.com/engine/network/packet-filtering-firewalls/",
      "site_name": "Docker Documentation"
    },
    "twitter_card": {
      "title": "Packet filtering and firewalls",
      "description": "How Docker works with packet filtering, iptables, and firewalls",
      "card": "summary_large_image",
      "domain": "https://docs.docker.com/",
      "site": "@docker_docs",
      "url": "https://twitter.com/docker_docs",
      "image:src": "https://docs.docker.com/images/thumbnail.webp",
      "image:alt": "Docker Documentation"
    },
    "schema_org": {
      "@context": "https://schema.org",
      "@type": "WebPage",
      "headline": "\"Packet filtering and firewalls\"",
      "description": "\"How Docker works with packet filtering, iptables, and firewalls\"",
      "url": "https://docs.docker.com/engine/network/packet-filtering-firewalls/"
    }
  }
}
```

Use this command to retrieve the URL for your function and use it as an API.

```
doctl sls fn get metadata/extract --url
```

You can use that API directly in your browser, with `curl` or with an API platform such as Postman.
Parameters may be passed as query parameters, or as JSON body. Here are some examples using `curl`.

```
curl `doctl sls fn get metadata/extract --url`?url=https://docs.docker.com/engine/network/packet-filtering-firewalls/#add-iptables-policies-before-dockers-rules
```

```
curl -H 'Content-Type: application/json' -d '{"url":"https://docs.docker.com/engine/network/packet-filtering-firewalls/#add-iptables-policies-before-dockers-rules"}' `doctl sls fn get metadata/extract --url`
```

### Learn More

You can learn more about Functions by reading the [Functions Documentation](https://docs.digitalocean.com/products/functions).
