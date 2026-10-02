package com.ai_nextgen_hacks.main.whatsapp.entity;

import com.ai_nextgen_hacks.main.whatsapp.enums.MessageDirection;
import com.ai_nextgen_hacks.main.whatsapp.enums.MessageStatus;
import com.ai_nextgen_hacks.main.whatsapp.enums.MessageType;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "whatsapp_messages")
public class WhatsAppMessage {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String phoneNumber;
    @Enumerated(EnumType.STRING)
    private MessageDirection direction;
    @Enumerated(EnumType.STRING)
    private MessageType messageType;
    @Column(length = 2000)
    private String messageContent;
    private String provider;
    private String providerMessageId;
    @Enumerated(EnumType.STRING)
    private MessageStatus status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    @PrePersist protected void onCreate() { createdAt = LocalDateTime.now(); updatedAt = LocalDateTime.now(); }
    @PreUpdate protected void onUpdate() { updatedAt = LocalDateTime.now(); }
    
    // Getters/Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getPhoneNumber() { return phoneNumber; }
    public void setPhoneNumber(String phoneNumber) { this.phoneNumber = phoneNumber; }
    public MessageDirection getDirection() { return direction; }
    public void setDirection(MessageDirection direction) { this.direction = direction; }
    public MessageType getMessageType() { return messageType; }
    public void setMessageType(MessageType messageType) { this.messageType = messageType; }
    public String getMessageContent() { return messageContent; }
    public void setMessageContent(String messageContent) { this.messageContent = messageContent; }
    public String getProvider() { return provider; }
    public void setProvider(String provider) { this.provider = provider; }
    public String getProviderMessageId() { return providerMessageId; }
    public void setProviderMessageId(String providerMessageId) { this.providerMessageId = providerMessageId; }
    public MessageStatus getStatus() { return status; }
    public void setStatus(MessageStatus status) { this.status = status; }
}
