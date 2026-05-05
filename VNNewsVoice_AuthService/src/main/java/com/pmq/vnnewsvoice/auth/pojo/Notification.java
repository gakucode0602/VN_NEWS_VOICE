package com.pmq.vnnewsvoice.auth.pojo;

import jakarta.persistence.*;
import java.io.Serializable;
import java.util.Date;
import java.util.Set;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "notification")
@Getter
@Setter
@NoArgsConstructor
public class Notification implements Serializable {

  private static final long serialVersionUID = 1L;

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id")
  private Long id;

  @Column(name = "title", nullable = false)
  private String title;

  @Column(name = "content", nullable = false)
  private String content;

  @Column(name = "is_read")
  private Boolean isRead;

  @Column(name = "created_at")
  @Temporal(TemporalType.TIMESTAMP)
  private Date createdAt;

  @JoinColumn(name = "user_id", referencedColumnName = "id")
  @ManyToOne(optional = false)
  private UserInfo userId;

  @OneToMany(cascade = CascadeType.ALL, mappedBy = "notificationId")
  private Set<NotificationRole> notificationRoleSet;

  public Notification(Long id) {
    this.id = id;
  }
}
