package com.ai_nextgen_hacks.main.whatsapp.service;

import com.ai_nextgen_hacks.main.whatsapp.entity.WhatsAppInteraction;
import com.ai_nextgen_hacks.main.whatsapp.entity.WhatsAppMessage;
import com.ai_nextgen_hacks.main.whatsapp.enums.InteractionType;
import com.ai_nextgen_hacks.main.whatsapp.enums.MessageDirection;
import com.ai_nextgen_hacks.main.whatsapp.enums.MessageStatus;
import com.ai_nextgen_hacks.main.whatsapp.enums.MessageType;
import com.ai_nextgen_hacks.main.whatsapp.repository.WhatsAppInteractionRepository;
import com.ai_nextgen_hacks.main.whatsapp.repository.WhatsAppMessageRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class WhatsAppWebhookService {

    @Autowired private WhatsAppMessageRepository messageRepository;
    @Autowired private WhatsAppInteractionRepository interactionRepository;
    @Autowired private RestTemplate restTemplate;

    public void processInboundMessage(String phoneNumber, String content, String providerMessageId) {
        // Save inbound message
        WhatsAppMessage msg = new WhatsAppMessage();
        msg.setPhoneNumber(phoneNumber);
        msg.setDirection(MessageDirection.INBOUND);
        msg.setMessageType(MessageType.CUSTOMER_RESPONSE);
        msg.setMessageContent(content);
        msg.setProviderMessageId(providerMessageId);
        msg.setStatus(MessageStatus.DELIVERED);
        msg = messageRepository.save(msg);

        // Deterministic Interpretation
        InteractionType type = interpretResponse(content);
        
        WhatsAppInteraction interaction = new WhatsAppInteraction();
        interaction.setWhatsappMessageId(msg.getId());
        interaction.setInteractionType(type);
        interaction.setResponseValue(content);
        interaction.setShipmentIdContext("SHP10045"); // For hackathon purposes, mock mapping
        interactionRepository.save(interaction);

        // Trigger Risk Recalculation via REST (to avoid circular deps in hackathon)
        System.out.println("Triggering Risk Recalculation for " + interaction.getShipmentIdContext());
        try {
            // Simulated REST call to recalculate endpoint
            // restTemplate.postForEntity("http://localhost:8080/api/v1/risk/recalculate/" + interaction.getShipmentIdContext(), null, String.class);
        } catch (Exception e) {
            // ignore for now
        }
    }
    
    public void processStatusUpdate(String providerMessageId, String newStatus) {
        WhatsAppMessage msg = messageRepository.findByProviderMessageId(providerMessageId);
        if (msg != null) {
            try {
                msg.setStatus(MessageStatus.valueOf(newStatus.toUpperCase()));
                messageRepository.save(msg);
            } catch (Exception e) {
                // Handle invalid status quietly
            }
        }
    }

    private InteractionType interpretResponse(String text) {
        if (text == null) return InteractionType.OTHER;
        String t = text.trim().toUpperCase();
        if (t.equals("YES") || t.equals("Y") || t.equals("OK") || t.equals("AVAILABLE") || t.equals("CONFIRM")) {
            return InteractionType.CONFIRM_AVAILABILITY;
        } else if (t.equals("RESCHEDULE") || t.equals("LATER") || t.equals("ANOTHER DAY")) {
            return InteractionType.RESCHEDULE;
        } else if (t.equals("PICKUP") || t.equals("HOLD")) {
            return InteractionType.PICKUP;
        }
        return InteractionType.OTHER;
    }
}
