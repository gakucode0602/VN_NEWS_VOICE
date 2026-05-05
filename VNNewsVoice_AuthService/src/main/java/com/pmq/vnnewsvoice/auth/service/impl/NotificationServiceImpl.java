package com.pmq.vnnewsvoice.auth.service.impl;

import com.pmq.vnnewsvoice.auth.pojo.Notification;
import com.pmq.vnnewsvoice.auth.repository.NotificationRepository;
import com.pmq.vnnewsvoice.auth.service.NotificationService;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class NotificationServiceImpl implements NotificationService {
  private final NotificationRepository notificationRepository;

  @Override
  @Transactional
  public Notification addNotification(Notification notification) {
    if (notification == null) {
      throw new IllegalArgumentException("Notification cannot be null");
    }
    return notificationRepository.save(notification);
  }

  @Override
  public Notification getNotificationById(Long id) {
    if (id == null) {
      return null;
    }
    return notificationRepository.findById(id).orElse(null);
  }

  @Override
  @Transactional
  public Notification updateNotification(Notification notification) {
    if (notification == null || notification.getId() == null) {
      throw new IllegalArgumentException("Notification or ID cannot be null");
    }
    if (!notificationRepository.existsById(notification.getId())) {
      throw new IllegalArgumentException("Notification not found with id: " + notification.getId());
    }
    return notificationRepository.save(notification);
  }

  @Override
  @Transactional
  public boolean deleteNotification(Long id) {
    if (id == null || !notificationRepository.existsById(id)) {
      return false;
    }
    notificationRepository.deleteById(id);
    return true;
  }

  @Override
  public long countUnreadNotifications() {
    return notificationRepository.countByIsReadFalse();
  }

  @Override
  public List<Notification> getNotificationsByUserId(Long userId) {
    if (userId == null) {
      return List.of();
    }
    return notificationRepository.findByUserId_IdOrderByCreatedAtDesc(userId);
  }

  @Override
  public List<Notification> getNotificationsByUserIdPaginated(Long userId, int page, int size) {
    if (userId == null || page < 0 || size <= 0) {
      return List.of();
    }
    return notificationRepository.findByUserId_IdOrderByCreatedAtDesc(
        userId, PageRequest.of(page, size));
  }
}
