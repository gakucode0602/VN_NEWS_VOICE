package com.pmq.vnnewsvoice.comment.pojo;

import jakarta.persistence.*;
import java.util.Date;
import java.util.Set;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "comment")
@Getter
@Setter
@NoArgsConstructor
public class Comment {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id")
  private Long id;

  @Column(name = "content", nullable = false, columnDefinition = "TEXT")
  private String content;

  // Cross-service ref to ArticleService article_db — no @ManyToOne, no FK
  @Column(name = "article_id", nullable = false, length = 64)
  private String articleId;

  // Cross-service ref to AuthService auth_db — no @ManyToOne, no FK
  @Column(name = "user_id", nullable = false)
  private Long userId;

  // Denormalized from JWT claim at write time.
  // Eventual consistency via RabbitMQ user.updated event (future work).
  @Column(name = "username", nullable = false)
  private String username;

  // Self-reference within comment_db — @ManyToOne is safe here (same DB)
  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "comment_reply_id", referencedColumnName = "id")
  private Comment commentReply;

  // Replies to this comment (children in the tree)
  @OneToMany(mappedBy = "commentReply", fetch = FetchType.LAZY)
  private Set<Comment> replies;

  @OneToMany(mappedBy = "comment", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
  private Set<CommentLike> commentLikes;

  @Column(name = "created_at")
  @Temporal(TemporalType.TIMESTAMP)
  private Date createdAt;

  // Soft delete — null means active, non-null means deleted
  @Column(name = "deleted_at")
  @Temporal(TemporalType.TIMESTAMP)
  private Date deletedAt;

  @Column(name = "hidden_by_article", nullable = false)
  private Boolean hiddenByArticle = false;

  @Column(name = "hidden_by_user", nullable = false)
  private Boolean hiddenByUser = false;

  public Comment(Long id) {
    this.id = id;
  }

  public boolean isDeleted() {
    return deletedAt != null;
  }
}
