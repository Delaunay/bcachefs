#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "bcachefs/bcachefs.h"

int main() {
    BCacheFS bchfs = {0};
    int      err   = BCacheFS_open(&bchfs, "mini_bcachefs.img");

    if (err) {
    } else {
        return 1;
    }

    struct bch_sb *                sb            = bchfs.sb;
    const struct bch_val *         bch_val       = NULL;
    const struct bch_btree_ptr_v2 *bch_btree_ptr = NULL;

    printf("sb_size: %llu\n", benz_bch_get_sb_size(sb));
    printf("btree_node_size: %llu\n", benz_bch_get_btree_node_size(sb));

    benz_print_uuid(&sb->magic);
    printf("\n");

    uint64_t bset_magic = __bset_magic(sb);
    uint64_t jset_magic = __jset_magic(sb);

    printf("bset_magic:");
    benz_print_hex(((const uint8_t *)&bset_magic) + 0, 4);
    printf("-");
    benz_print_hex(((const uint8_t *)&bset_magic) + 4, 4);
    printf("\n");

    printf("bset_magic:%llu\n", bset_magic);
    printf("jset_magic:");
    benz_print_hex(((const uint8_t *)&jset_magic) + 0, 4);
    printf("-");
    benz_print_hex(((const uint8_t *)&jset_magic) + 4, 4);
    printf("\n");
    printf("jset_magic:%llu\n", jset_magic);

    BCacheFS_iterator bchfs_iter = {0};
    BCacheFS_iter(&bchfs, &bchfs_iter, BTREE_ID_extents);

    bch_val       = BCacheFS_iter_next(&bchfs, &bchfs_iter);
    bch_btree_ptr = NULL;

    for (; bch_val; bch_val = BCacheFS_iter_next(&bchfs, &bchfs_iter)) {

        const struct bkey *bkey = bchfs_iter.bkey;
        printf(" - bkey: u:%u, f:%u, t:%u, s:%u, o:%llu\n", bkey->u64s, bkey->format, bkey->type,
               bkey->size, bkey->p.offset);

        BCacheFS_extent extend = BCacheFS_iter_make_extent(&bchfs, &bchfs_iter);
        printf("    - extend: fo:%lu, i:%lu, of:%lu, s:%lu\n", extend.file_offset, extend.inode,
               extend.offset, extend.size);
    }
    BCacheFS_iter_fini(&bchfs, &bchfs_iter);
    BCacheFS_iter(&bchfs, &bchfs_iter, BTREE_ID_dirents);
    bch_val = BCacheFS_iter_next(&bchfs, &bchfs_iter);
    for (; bch_val; bch_val = BCacheFS_iter_next(&bchfs, &bchfs_iter)) {
        const struct bkey *bkey = bchfs_iter.bkey;
        printf(" - bkey: u:%u, f:%u, t:%u, s:%u, o:%llu\n", bkey->u64s, bkey->format, bkey->type,
               bkey->size, bkey->p.offset);

        BCacheFS_dirent dirent = BCacheFS_iter_make_dirent(&bchfs, &bchfs_iter);
        printf("    - dirent: p:%llu, i:%llu, t:%u, %s\n", dirent.parent_inode, dirent.inode,
               dirent.type, dirent.name);
    }
    BCacheFS_iter_fini(&bchfs, &bchfs_iter);
    BCacheFS_fini(&bchfs);
    return 0;
}
