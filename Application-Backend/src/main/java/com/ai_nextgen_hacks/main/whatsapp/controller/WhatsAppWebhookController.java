package com.ai_nextgen_hacks.main.whatsapp.controller;

import com.ai_nextgen_hacks.main.whatsapp.config.WhatsAppProperties;
import com.ai_nextgen_hacks.main.whatsapp.service.WhatsAppWebhookService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/webhooks/whatsapp")
public class WhatsAppWebhookController {

    @Autowired private WhatsAppProperties props;
    @Autowired private WhatsAppWebhookService webhookService;

    @GetMapping
    public ResponseEntity<String> verifyWebhook(
            @RequestParam(name = "hub.mode", required = false) String mode,
            @RequestParam(name = "hub.verify_token", required = false) String token,
            @RequestParam(name = "hub.challenge", required = false) String challenge) {
        
        if ("subscribe".equals(mode) && props.getVerifyToken().equals(token)) {
            return ResponseEntity.ok(challenge);
        }
        return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
    }

    @PostMapping
    public ResponseEntity<String> receiveWebhook(@RequestBody Map<String, Object> payload) {
        // Mock processing for hackathon - extract message from Meta's complex JSON
        try {
            // Simplified logic assuming payload contains mock test data
            if (payload.containsKey("type") && "inbound".equals(payload.get("type"))) {
                String phone = (String) payload.get("phoneNumber");
                String text = (String) payload.get("text");
                String msgId = (String) payload.getOrDefault("messageId", "inbound-" + System.currentTimeMillis());
                webhookService.processInboundMessage(phone, text, msgId);
            }
        } catch (Exception e) {
            System.err.println("Webhook error: " + e.getMessage());
        }
        return ResponseEntity.ok("EVENT_RECEIVED");
    }
}
