package com.pmq.vnnewsvoice.comment.pojo;

import jakarta.persistence.*;
import java.util.Date;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "comment_like")
@Getter
@Setter
@NoArgsConstructor
public class CommentLike {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id")
  private Long id;

  // FK within comment_db — safe to use @ManyToOne
  @ManyToOne(optional = false, fetch = FetchType.LAZY)
  @JoinColumn(name = "comment_id", referencedColumnName = "id")
  private Comment comment;

  // Cross-service ref to AuthService auth_db — no @ManyToOne, no FK
  @Column(name = "user_id", nullable = false)
  private Long userId;

  @Column(name = "created_at")
  @Temporal(TemporalType.TIMESTAMP)
  private Date createdAt;

  public CommentLike(Long id) {
    this.id = id;
  }
}
