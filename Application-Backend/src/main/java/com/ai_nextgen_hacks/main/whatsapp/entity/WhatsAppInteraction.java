package com.ai_nextgen_hacks.main.whatsapp.entity;

import com.ai_nextgen_hacks.main.whatsapp.enums.InteractionType;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "whatsapp_interactions")
public class WhatsAppInteraction {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private Long whatsappMessageId;
    @Enumerated(EnumType.STRING)
    private InteractionType interactionType;
    private String responseValue;
    private LocalDateTime createdAt;
    private String shipmentIdContext;

    @PrePersist protected void onCreate() { createdAt = LocalDateTime.now(); }
    
    // Getters/Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getWhatsappMessageId() { return whatsappMessageId; }
    public void setWhatsappMessageId(Long whatsappMessageId) { this.whatsappMessageId = whatsappMessageId; }
    public InteractionType getInteractionType() { return interactionType; }
    public void setInteractionType(InteractionType interactionType) { this.interactionType = interactionType; }
    public String getResponseValue() { return responseValue; }
    public void setResponseValue(String responseValue) { this.responseValue = responseValue; }
    public String getShipmentIdContext() { return shipmentIdContext; }
    public void setShipmentIdContext(String shipmentIdContext) { this.shipmentIdContext = shipmentIdContext; }
}
