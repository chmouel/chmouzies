(defun ppr-magit-read-remote-branch (prompt remote)
  (magit-completing-read prompt (magit-remote-list-branches remote)))

(defun ppr-magit-read-remote (prompt &optional exclude)
  (magit-completing-read prompt (magit-list-remotes)
                         (lambda (elt) (not (string= elt exclude)))))

(let* ((origin-remote (magit-read-remote "Base Remote"))
       (user-remote (ppr-magit-read-remote "User Remote" origin-remote))
       (current-branch (magit-get-current-branch))
       (origin-remote-branch
        (ppr-magit-read-remote-branch
         (format "Base remote branch on %s" origin-remote)
         origin-remote)))
  (if (yes-or-no-p
       (format "Push force current branch %s to user remote %s" current-branch user-remote))
      (magit-run-git-async "push" "-v" "-f" user-remote current-branch))
