package com.ai_nextgen_hacks.main.whatsapp.service;

import com.ai_nextgen_hacks.main.recommendation.entity.RecommendationEntity;
import com.ai_nextgen_hacks.main.whatsapp.config.WhatsAppProperties;
import com.ai_nextgen_hacks.main.whatsapp.dto.SendWhatsAppMessageResponse;
import com.ai_nextgen_hacks.main.whatsapp.entity.WhatsAppMessage;
import com.ai_nextgen_hacks.main.whatsapp.enums.MessageDirection;
import com.ai_nextgen_hacks.main.whatsapp.enums.MessageStatus;
import com.ai_nextgen_hacks.main.whatsapp.enums.MessageType;
import com.ai_nextgen_hacks.main.whatsapp.provider.WhatsAppProvider;
import com.ai_nextgen_hacks.main.whatsapp.repository.WhatsAppMessageRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;

@Service
public class WhatsAppService {

    @Autowired private WhatsAppProperties props;
    @Autowired private ApplicationContext context;
    @Autowired private WhatsAppMessageRepository messageRepository;

    private WhatsAppProvider provider;

    @PostConstruct
    public void init() {
        if ("meta".equalsIgnoreCase(props.getProvider())) {
            this.provider = context.getBean("metaWhatsAppProvider", WhatsAppProvider.class);
        } else {
            this.provider = context.getBean("mockWhatsAppProvider", WhatsAppProvider.class);
        }
    }

    public SendWhatsAppMessageResponse sendMessage(String phoneNumber, String messageContent, RecommendationEntity recContext) {
        WhatsAppMessage msg = new WhatsAppMessage();
        msg.setPhoneNumber(phoneNumber);
        msg.setDirection(MessageDirection.OUTBOUND);
        msg.setMessageType(MessageType.AVAILABILITY_REQUEST);
        msg.setMessageContent(messageContent);
        msg.setStatus(MessageStatus.PENDING);
        msg = messageRepository.save(msg);

        SendWhatsAppMessageResponse resp = provider.sendMessage(phoneNumber, messageContent);
        
        msg.setProvider(resp.provider());
        msg.setProviderMessageId(resp.providerMessageId());
        msg.setStatus(resp.status().equals("SENT") ? MessageStatus.SENT : MessageStatus.FAILED);
        messageRepository.save(msg);
        
        return resp;
    }
    
    public SendWhatsAppMessageResponse sendRawMessage(String phoneNumber, String messageContent) {
        return sendMessage(phoneNumber, messageContent, null);
    }
}
