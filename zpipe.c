#include <linux/types.h>
#include <linux/file.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/module.h>

#include "../zdce.h"

#define CHUNK 16384
#define CHUNK_OUT (CHUNK * 5)
#define CHUNK_OUT_INF (CHUNK * 25)

MODULE_LICENSE("Dual BSD/GPL");

static char *in_file;
module_param(in_file, charp, 0);
MODULE_PARM_DESC(in_file, " Input file to (de)compress");

static char *out_file;
module_param(out_file, charp, 0);
MODULE_PARM_DESC(out_file, " Output file result of (de)compression");

static int mode;
module_param(mode, int, 0);
MODULE_PARM_DESC(mode, " Select compression (0) or decompression (1). Default = 0");

#define IAM_HERE() /*pr_err("I am on line %d\n", __LINE__)*/

static int dce_deflate(z_stream *stream, int flush)
{
	int ret;
	struct device *dce_device = fsl_dce_get_device();
	dma_addr_t old_next_in = stream->next_in, old_next_out = stream->next_out;
	size_t old_avail_in = stream->avail_in, old_avail_out = stream->avail_out;

	stream->next_in = dma_map_single(dce_device, (void *)old_next_in,
					old_avail_in, DMA_BIDIRECTIONAL);
	if (!stream->next_in) {
		pr_err("Unable to translate virtual address to physical\n");
		return Z_STREAM_ERROR;
	}
	
	stream->next_out = dma_map_single(dce_device, (void *)old_next_out,
					old_avail_out, DMA_BIDIRECTIONAL);
	if (!stream->next_out) {
		pr_err("Unable to translate virtual address to physical\n");
		return Z_STREAM_ERROR;
	}

        pr_info("DEBUG WK before dce_deflate: stream->avail_in=%lu, stream->avail_out=%lu\n", stream->avail_in, stream->avail_out);

	ret = deflate(stream, flush);

        pr_info("DEBUG WK after dce_deflate: stream->avail_in=%lu, stream->avail_out=%lu\n", stream->avail_in, stream->avail_out);

	dma_unmap_single(dce_device, old_next_in, old_avail_in, DMA_BIDIRECTIONAL);
	dma_unmap_single(dce_device, old_next_out, old_avail_out, DMA_BIDIRECTIONAL);

	stream->next_in = (dma_addr_t)phys_to_virt(stream->next_in);
	WARN_ON(!stream->next_in);
	stream->next_out = (dma_addr_t)phys_to_virt(stream->next_out);
	WARN_ON(!stream->next_out);
	return ret;
}

/* Compress from file source to file dest until EOF on source.
   def() returns Z_OK on success, Z_MEM_ERROR if memory could not be
   allocated for processing, Z_STREAM_ERROR if an invalid compression
   level is supplied, Z_VERSION_ERROR if the version of zlib.h and the
   version of the library linked do not match, or Z_ERRNO if there is
   an error reading or writing the files. */
static int def(const char *source, const char *dest, int level)
{
	int ret = Z_ERRNO, flush;
	unsigned have;
	z_stream strm;
	unsigned char *in;
	unsigned char *out;
	struct file *filpi = NULL, *filpo = NULL;
	struct inode *inode = NULL;
	loff_t position_in = 0, position_out = 0, size, total_read = 0;
	mm_segment_t oldfs = get_fs();

	IAM_HERE();
	filpi = filp_open(source, O_RDONLY | O_LARGEFILE, 0);
	if (IS_ERR(filpi)) {
		pr_err("unable to open file: %s\n", source);
		return PTR_ERR(filpi);
	}
	IAM_HERE();

	filpo = filp_open(dest, O_CREAT | O_WRONLY | O_LARGEFILE, 0666);
	IAM_HERE();
	if (IS_ERR(filpo)) {
		pr_err("unable to open file: %s\n", dest);
		goto fail_filpo_open;
	}
	IAM_HERE();

	inode = filpi->f_path.dentry->d_inode;
	if ((!S_ISREG(inode->i_mode) && !S_ISBLK(inode->i_mode))) {
		pr_err("invalid file type: %s\n", source);
		goto fail_file_reads;
	}
	IAM_HERE();

	size = i_size_read(inode->i_mapping->host);
	if (size < 0) {
		pr_err("unable to find file size: %s\n", source);
		ret = (int)size;
		goto fail_file_reads;
	}
	IAM_HERE();
	set_fs(KERNEL_DS);
	IAM_HERE();

	/* allocate deflate state */
	strm.zalloc = Z_NULL;
	strm.zfree = Z_NULL;
	strm.opaque = Z_NULL;
	strm.avail_in = 0;
	strm.next_in = Z_NULL;
	ret = deflateInit(&strm, level);
	IAM_HERE();
	if (ret != Z_OK) {
		pr_err("deflateInit failed\n");
		goto fail_file_reads;
	}

	in = strm.zalloc(CHUNK, GFP_KERNEL);
	if (!in) {
		pr_err("Failed to allocate input memory\n");
		goto fail_in_alloc;
	}

	out = strm.zalloc(CHUNK_OUT, GFP_KERNEL); /* 5 * the size of input to make
						sure we never have a buffer over
						run because we do not handle it
						currently */
	if (!out) {
		pr_err("Failed to allocate output memory\n");
		goto fail_out_alloc;
	}

	/* compress until end of file */
	do {
		strm.avail_in = vfs_read(filpi, in, CHUNK, &position_in);
		if (IS_ERR(filpi)) {
			(void)deflateEnd(&strm);
			ret = Z_ERRNO;
			goto fail;
		}
		total_read += strm.avail_in;
		IAM_HERE();
		WARN_ON(total_read > size);
		flush = (size == total_read) ? Z_FINISH : Z_NO_FLUSH;
		strm.next_in = (dma_addr_t)in;

		/* run deflate() on input until output buffer not full, finish
		 * compression if all of source has been read in */
		do {
			int written;
			strm.avail_out = CHUNK_OUT;
			strm.next_out = (dma_addr_t)out;
			IAM_HERE();
			ret = dce_deflate(&strm, flush);    /* no bad return value */
			if (ret == Z_STREAM_ERROR) {
				pr_err("error: Stream state is Z_STREAM_ERROR\n");
				ret = Z_ERRNO;
				goto fail;
			}
			have = CHUNK_OUT - strm.avail_out;
			IAM_HERE();
			written = vfs_write(filpo, out, have, &position_out);
			IAM_HERE();
			if (written != have) {
				(void)deflateEnd(&strm);
				ret = Z_ERRNO;
				goto fail;
			}
			IAM_HERE();
		} while (strm.avail_out == 0);
		IAM_HERE();
		WARN_ON(strm.avail_in != 0);     /* all input will be used */
		IAM_HERE();

		/* done when last data in file processed */
	} while (flush != Z_FINISH);
	WARN_ON(ret != Z_STREAM_END);        /* stream will be complete */
	IAM_HERE();

	/* clean up and return */
fail:
	strm.zfree(out);
fail_out_alloc:
	strm.zfree(in);
fail_in_alloc:
	(void)deflateEnd(&strm);
fail_file_reads:
	fput(filpo);
fail_filpo_open:
	fput(filpi);
	IAM_HERE();
	set_fs(oldfs);
	return ret == Z_STREAM_END ? Z_OK : Z_DATA_ERROR;
}

static int dce_inflate(z_stream *stream, int flush)
{
	int ret;
	struct device *dce_device = fsl_dce_get_device();
	dma_addr_t old_next_in = stream->next_in, old_next_out = stream->next_out;
	size_t old_avail_in = stream->avail_in, old_avail_out = stream->avail_out;

	stream->next_in = dma_map_single(dce_device, (void *)old_next_in,
					old_avail_in, DMA_BIDIRECTIONAL);
	if (!stream->next_in) {
		pr_err("Unable to translate virtual address to physical\n");
		return Z_STREAM_ERROR;
	}
	
	stream->next_out = dma_map_single(dce_device, (void *)old_next_out,
					old_avail_out, DMA_BIDIRECTIONAL);
	if (!stream->next_out) {
		pr_err("Unable to translate virtual address to physical\n");
		return Z_STREAM_ERROR;
	}

        pr_info("DEBUG WK before dce_inflate: stream->avail_in=%lu, stream->avail_out=%lu\n", stream->avail_in, stream->avail_out);

	ret = inflate(stream, flush);

        pr_info("DEBUG WK after dce_inflate: stream->avail_in=%lu, stream->avail_out=%lu\n", stream->avail_in, stream->avail_out);

	dma_unmap_single(dce_device, old_next_in, old_avail_in, DMA_BIDIRECTIONAL);
	dma_unmap_single(dce_device, old_next_out, old_avail_out, DMA_BIDIRECTIONAL);

	stream->next_in = (dma_addr_t)phys_to_virt(stream->next_in);
	WARN_ON(!stream->next_in);
	stream->next_out = (dma_addr_t)phys_to_virt(stream->next_out);
	WARN_ON(!stream->next_out);
	return ret;
}

/* Decompress from file source to file dest until stream ends or EOF.
   inf() returns Z_OK on success, Z_MEM_ERROR if memory could not be
   allocated for processing, Z_DATA_ERROR if the deflate data is
   invalid or incomplete, Z_VERSION_ERROR if the version of zlib.h and
   the version of the library linked do not match, or Z_ERRNO if there
   is an error reading or writing the files. */
static int inf(const char *source, const char *dest)
{
	int ret = Z_ERRNO, flush;
	unsigned have;
	z_stream strm;
	unsigned char *in;
	unsigned char *out;
	struct file *filpi = NULL, *filpo = NULL;
	struct inode *inode = NULL;
	loff_t position_in = 0, position_out = 0, size, total_read = 0;
	mm_segment_t oldfs = get_fs();

	filpi = filp_open(source, O_RDONLY | O_LARGEFILE, 0);
	if (IS_ERR(filpi)) {
		pr_err("unable to open file: %s\n", source);
		return PTR_ERR(filpi);
	}
	IAM_HERE();

	filpo = filp_open(dest, O_CREAT | O_WRONLY | O_LARGEFILE, 0666);
	IAM_HERE();
	if (IS_ERR(filpo)) {
		pr_err("unable to open file: %s\n", dest);
		goto fail_filpo_open;
	}
	IAM_HERE();

	inode = filpi->f_path.dentry->d_inode;
	if ((!S_ISREG(inode->i_mode) && !S_ISBLK(inode->i_mode))) {
		pr_err("invalid file type: %s\n", source);
		goto fail_file_reads;
	}
	IAM_HERE();
	size = i_size_read(inode->i_mapping->host);
	if (size < 0) {
		pr_err("unable to find file size: %s\n", source);
		ret = (int)size;
		goto fail_file_reads;
	}

	IAM_HERE();
	set_fs(KERNEL_DS);
	IAM_HERE();

	/* allocate inflate state */
	strm.zalloc = Z_NULL;
	strm.zfree = Z_NULL;
	strm.opaque = Z_NULL;
	strm.avail_in = 0;
	strm.next_in = Z_NULL;
	ret = inflateInit(&strm);
	if (ret != Z_OK) {
		pr_err("inflateInit failed\n");
		goto fail_file_reads;
	}

	in = strm.zalloc(CHUNK, GFP_KERNEL);
	if (!in) {
		pr_err("Failed to allocate input memory\n");
		goto fail_in_alloc;
	}

	/* many * the size of input to make sure we never have a
	 * buffer over run because we do not handle it currently */
	out = strm.zalloc(CHUNK_OUT_INF, GFP_KERNEL);
	if (!out) {
		pr_err("Failed to allocate output memory\n");
		goto fail_out_alloc;
	}

	/* decompress until deflate stream ends or end of file */
	do {
		strm.avail_in = vfs_read(filpi, in, CHUNK, &position_in);
		if (IS_ERR(filpi)) {
			(void)inflateEnd(&strm);
			ret = Z_ERRNO;
			goto fail;
		}
		if (strm.avail_in == 0)
			break;
		total_read += strm.avail_in;
		WARN_ON(total_read > size);
		strm.next_in = (dma_addr_t)in;
		flush = (size == total_read) ? Z_FINISH : Z_NO_FLUSH;
		

		/* run inflate() on input until output buffer not full */
		do {
			int written;
			strm.avail_out = CHUNK_OUT_INF;
			strm.next_out = (dma_addr_t)out;
			ret = dce_inflate(&strm, Z_NO_FLUSH);
			WARN_ON(ret == Z_STREAM_ERROR);  /* state not clobbered */
			switch (ret) {
				case Z_NEED_DICT:
					ret = Z_DATA_ERROR;     /* and fall through */
				case Z_DATA_ERROR:
				case Z_MEM_ERROR:
					(void)inflateEnd(&strm);
					ret = Z_ERRNO;
					goto fail;
			}
			have = CHUNK_OUT_INF - strm.avail_out;
			written = vfs_write(filpo, out, have, &position_out);
			if (written != have) {
				(void)inflateEnd(&strm);
				ret = Z_ERRNO;
				goto fail;
			}
		} while (strm.avail_out == 0);
		/* can't check avail_in == 0; could be embedded compressed data */

		/* done when inflate() says it's done */
	} while (ret != Z_STREAM_END);

	/* clean up and return */
fail:
	strm.zfree(out);
fail_out_alloc:
	strm.zfree(in);
fail_in_alloc:
	(void)inflateEnd(&strm);
fail_file_reads:
	fput(filpo);
fail_filpo_open:
	fput(filpi);
	set_fs(oldfs);
	return ret == Z_STREAM_END ? Z_OK : Z_DATA_ERROR;
}


/* report a zlib or i/o error */
void zerr(int ret)
{
	pr_err("zpipe: ");
	switch (ret) {
		case Z_ERRNO:
			pr_err("error reading stdin\n");
			pr_err("error writing stdout\n");
			break;
		case Z_STREAM_ERROR:
			pr_err("invalid compression level\n");
			break;
		case Z_DATA_ERROR:
			pr_err("invalid or incomplete deflate data\n");
			break;
		case Z_MEM_ERROR:
			pr_err("out of memory\n");
			break;
		case Z_VERSION_ERROR:
			pr_err("zlib version mismatch!\n");
	}
}

int dce_zpipe_test_init(void)
{
	int ret;

	if (in_file == NULL || out_file == NULL) {
		pr_err("Must supply valid file names\n");
		return -EINVAL;
	}

	pr_info("zpipe about to start test. The input file is %s, the output file is %s\n",
			in_file, out_file);

	/* do compression if mode = 0 */
	if (!mode)
		ret = def(in_file, out_file, Z_DEFAULT_COMPRESSION);
	else /* else do decompression */
		ret = inf(in_file, out_file);
	if (ret != Z_OK)
		zerr(ret);
	pr_info("Finished test\n");
	return ret;
}

static void __exit dce_zpipe_test_exit(void)
{
	pr_info("%s\n", __func__);
}

module_init(dce_zpipe_test_init);
module_exit(dce_zpipe_test_exit);
