package com.ai_nextgen_hacks.main.whatsapp.controller;

import com.ai_nextgen_hacks.main.whatsapp.dto.SendWhatsAppMessageRequest;
import com.ai_nextgen_hacks.main.whatsapp.dto.SendWhatsAppMessageResponse;
import com.ai_nextgen_hacks.main.whatsapp.entity.WhatsAppInteraction;
import com.ai_nextgen_hacks.main.whatsapp.entity.WhatsAppMessage;
import com.ai_nextgen_hacks.main.whatsapp.repository.WhatsAppInteractionRepository;
import com.ai_nextgen_hacks.main.whatsapp.repository.WhatsAppMessageRepository;
import com.ai_nextgen_hacks.main.whatsapp.service.WhatsAppService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/v1/whatsapp")
public class WhatsAppController {

    @Autowired private WhatsAppService whatsAppService;
    @Autowired private WhatsAppMessageRepository messageRepository;
    @Autowired private WhatsAppInteractionRepository interactionRepository;

    @PostMapping("/messages")
    public ResponseEntity<SendWhatsAppMessageResponse> sendMessage(@RequestBody SendWhatsAppMessageRequest request) {
        return ResponseEntity.ok(whatsAppService.sendRawMessage(request.phoneNumber(), request.message()));
    }

    @GetMapping("/messages/{phoneNumber}")
    public ResponseEntity<List<WhatsAppMessage>> getMessages(@PathVariable String phoneNumber) {
        return ResponseEntity.ok(messageRepository.findByPhoneNumberOrderByCreatedAtDesc(phoneNumber));
    }
}
