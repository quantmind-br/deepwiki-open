# Codemap Feature - Smoke Test Checklist

## Pre-requisites

- [ ] Backend server running (`python -m api.api`)
- [ ] Frontend server running (`npm run dev`)
- [ ] Valid repository URL for testing
- [ ] API keys configured (Google AI or other provider)

## Test Scenarios

### 1. Basic Generation

- [ ] Navigate to `/{owner}/{repo}/codemap`
- [ ] Enter query: "Show me the overall architecture"
- [ ] Click Generate / Press Enter
- [ ] Verify progress bar appears
- [ ] Verify progress updates show different stages
- [ ] Verify codemap renders successfully
- [ ] Verify trace guide is displayed

### 2. Graph Interaction

- [ ] Click on a node in the graph
- [ ] Verify node inspector panel opens
- [ ] Verify node details are correct (type, location, description)
- [ ] Click "Navigate to Code" link
- [ ] Verify it opens correct file/location (if applicable)
- [ ] Hover over different nodes
- [ ] Verify hover highlighting works

### 3. View Controls

- [ ] Test zoom in button
- [ ] Test zoom out button
- [ ] Test fit view button
- [ ] Test pan (drag) functionality
- [ ] Switch between view modes (graph/trace/split)
- [ ] Verify each mode renders correctly

### 4. Trace Guide

- [ ] Expand/collapse trace sections
- [ ] Click on node references in trace guide
- [ ] Verify node highlighting in graph
- [ ] Verify markdown content renders correctly
- [ ] Verify code snippets are syntax highlighted

### 5. History

- [ ] Generate multiple codemaps
- [ ] Click History button
- [ ] Verify previous codemaps are listed
- [ ] Select a previous codemap
- [ ] Verify it loads correctly

### 6. Share Functionality

- [ ] Click Share button
- [ ] Verify share URL is generated
- [ ] Copy share URL
- [ ] Open share URL in incognito/new browser
- [ ] Verify shared codemap loads correctly

### 7. Export

- [ ] Export as HTML
- [ ] Verify HTML file downloads
- [ ] Open HTML file and verify it renders
- [ ] Export as Mermaid
- [ ] Verify .mmd file downloads
- [ ] Export as JSON
- [ ] Verify JSON structure is correct

### 8. Error Handling

- [ ] Test with invalid repository URL
- [ ] Verify error message is displayed
- [ ] Test with rate limit exceeded (if possible)
- [ ] Verify rate limit message is shown
- [ ] Test network disconnect during generation
- [ ] Verify appropriate error handling

### 9. Wiki Integration

- [ ] Navigate to wiki page (`/{owner}/{repo}`)
- [ ] Verify "Codemap" link in header
- [ ] Click Codemap link
- [ ] Verify navigation to codemap page
- [ ] Verify query parameters preserved
- [ ] Verify "Explore Codemap" button in sidebar

### 10. Performance

- [ ] Test with large repository (1000+ files)
- [ ] Verify generation completes within reasonable time
- [ ] Verify UI remains responsive during generation
- [ ] Verify graph rendering is smooth with 50+ nodes

## API Endpoints Verification

### REST API

- [ ] `POST /api/codemap/generate` - Returns codemap ID
- [ ] `GET /api/codemap/{id}` - Returns full codemap
- [ ] `GET /api/codemap/list/all` - Lists all codemaps
- [ ] `GET /api/codemap/repo/{owner}/{repo}` - Lists repo codemaps
- [ ] `POST /api/codemap/{id}/share` - Generates share token
- [ ] `GET /api/codemap/shared/{token}` - Gets shared codemap
- [ ] `DELETE /api/codemap/{id}` - Deletes codemap
- [ ] `GET /api/codemap/{id}/export/html` - Exports HTML
- [ ] `GET /api/codemap/{id}/export/mermaid` - Exports Mermaid
- [ ] `GET /api/codemap/{id}/export/json` - Exports JSON

### WebSocket

- [ ] Connect to `ws://localhost:8001/ws/codemap`
- [ ] Send generation request
- [ ] Receive progress updates
- [ ] Receive completion message

## Security Checks

- [ ] Tokens are not logged in console
- [ ] Tokens are not visible in API responses
- [ ] Rate limiting prevents excessive requests
- [ ] Share tokens expire after configured time

## Sign-off

| Tester | Date | Pass/Fail | Notes |
|--------|------|-----------|-------|
|        |      |           |       |
