package com.pmq.vnnewsvoice.auth.repository;

import com.pmq.vnnewsvoice.auth.pojo.Notification;
import java.util.List;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface NotificationRepository extends JpaRepository<Notification, Long> {
  long countByIsReadFalse();

  long countByUserId_Id(Long userId);

  List<Notification> findByUserId_IdOrderByCreatedAtDesc(Long userId);

  List<Notification> findByUserId_IdOrderByCreatedAtDesc(Long userId, Pageable pageable);
}
