package com.ai_nextgen_hacks.main.whatsapp.repository;
import com.ai_nextgen_hacks.main.whatsapp.entity.WhatsAppMessage;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface WhatsAppMessageRepository extends JpaRepository<WhatsAppMessage, Long> {
    List<WhatsAppMessage> findByPhoneNumberOrderByCreatedAtDesc(String phoneNumber);
    WhatsAppMessage findByProviderMessageId(String providerMessageId);
}
