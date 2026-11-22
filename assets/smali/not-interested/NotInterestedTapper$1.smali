.class Lcom/gramforge/NotInterestedTapper$1;
.super Ljava/lang/Object;
.source "NotInterestedTapper.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/gramforge/NotInterestedTapper;->schedule(Landroid/view/View;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field private tries:I

.field final synthetic val$handler:Landroid/os/Handler;

.field final synthetic val$origin:Landroid/view/View;


# direct methods
.method constructor <init>(Landroid/view/View;Landroid/os/Handler;)V
    .locals 0
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 25
    iput-object p1, p0, Lcom/gramforge/NotInterestedTapper$1;->val$origin:Landroid/view/View;

    iput-object p2, p0, Lcom/gramforge/NotInterestedTapper$1;->val$handler:Landroid/os/Handler;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 3

    .line 29
    const-string v0, "GramForge"

    :try_start_0
    iget-object v1, p0, Lcom/gramforge/NotInterestedTapper$1;->val$origin:Landroid/view/View;

    invoke-static {v1}, Lcom/gramforge/NotInterestedTapper;->access$000(Landroid/view/View;)Z

    move-result v1

    if-eqz v1, :cond_0

    .line 30
    const-string v1, "Native Not interested chosen"

    invoke-static {v0, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 31
    return-void

    .line 36
    :cond_0
    nop

    .line 37
    iget v1, p0, Lcom/gramforge/NotInterestedTapper$1;->tries:I

    add-int/lit8 v1, v1, 0x1

    iput v1, p0, Lcom/gramforge/NotInterestedTapper$1;->tries:I

    const/16 v2, 0xf

    if-ge v1, v2, :cond_1

    iget-object v0, p0, Lcom/gramforge/NotInterestedTapper$1;->val$handler:Landroid/os/Handler;

    const-wide/16 v1, 0x8c

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_0

    .line 38
    :cond_1
    const-string v1, "Not interested menu not found"

    invoke-static {v0, v1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 39
    :goto_0
    return-void

    .line 33
    :catch_0
    move-exception v1

    .line 34
    const-string v2, "Not interested menu lookup failed"

    invoke-static {v0, v2, v1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 35
    return-void
.end method
