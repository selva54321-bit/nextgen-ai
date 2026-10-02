package com.ai_nextgen_hacks.main.whatsapp.repository;
import com.ai_nextgen_hacks.main.whatsapp.entity.WhatsAppInteraction;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface WhatsAppInteractionRepository extends JpaRepository<WhatsAppInteraction, Long> {
    List<WhatsAppInteraction> findByShipmentIdContextOrderByCreatedAtDesc(String shipmentId);
}
